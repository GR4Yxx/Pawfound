import math
import os
import smtplib
import uuid
import base64
from contextlib import asynccontextmanager
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional

import chromadb
from dotenv import load_dotenv
from fastapi import BackgroundTasks, Depends, FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response

from auth import get_current_user, router as auth_router
from database import Dog, DogPhoto, Message, SessionLocal, User, init_db
from embedder import get_embedding, predict_breed

load_dotenv()

_CORS_ORIGINS = [o.strip() for o in os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:5173").split(",")]
_CHROMA_PATH = os.getenv("CHROMA_PATH", "/chroma_data")
# Minimum cosine similarity (0–1) for a result to appear in /match responses
SIMILARITY_THRESHOLD = float(os.getenv("SIMILARITY_THRESHOLD", "0.45"))
# Minimum cosine similarity to trigger an automatic inbox notification
NOTIFY_THRESHOLD = float(os.getenv("NOTIFY_THRESHOLD", "0.70"))

# SMTP config (all optional — notifications silently skipped if SMTP_HOST is empty)
SMTP_HOST = os.getenv("SMTP_HOST", "")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASS = os.getenv("SMTP_PASS", "")
SMTP_FROM = os.getenv("SMTP_FROM", "Pawfound <noreply@pawfound.app>")
APP_BASE_URL = os.getenv("APP_BASE_URL", "http://localhost")


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(title="Pawfound API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)

_chroma_client = chromadb.PersistentClient(path=_CHROMA_PATH)
# cosine space: distances are 1 - similarity, so similarity = 1 - distance
_collection = _chroma_client.get_or_create_collection(
    name="dogs",
    metadata={"hnsw:space": "cosine"},
)


def _image_url(request: Request, chroma_id: str) -> str:
    # Respect X-Forwarded-Host when behind nginx proxy
    host = request.headers.get("x-forwarded-host") or request.headers.get("host") or "localhost"
    scheme = request.headers.get("x-forwarded-proto", "http")
    return f"{scheme}://{host}/api/image/{chroma_id}"


@app.get("/image/{chroma_id}")
async def get_image(chroma_id: str):
    result = _collection.get(ids=[chroma_id], include=["metadatas"])
    if not result["ids"]:
        raise HTTPException(status_code=404, detail="Image not found")
    meta = result["metadatas"][0]
    image_b64 = meta.get("image_b64")
    if not image_b64:
        raise HTTPException(status_code=404, detail="Image not found")
    content_type = meta.get("content_type", "image/jpeg")
    image_bytes = base64.b64decode(image_b64)
    return Response(content=image_bytes, media_type=content_type, headers={
        "Cache-Control": "public, max-age=31536000, immutable",
    })


@app.post("/identify")
async def identify_breed(image: UploadFile = File(...)):
    """Return top-3 breed predictions for an uploaded image."""
    image_bytes = await image.read()
    try:
        predictions = predict_breed(image_bytes, top_k=3)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Identification failed: {e}")
    return {"predictions": predictions}


def _haversine_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlng = math.radians(lng2 - lng1)
    a = math.sin(dlat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlng / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def _send_match_email(to_email: str, to_dog_name: str, new_dog_name: str, similarity: float, new_dog_id: str) -> None:
    if not SMTP_HOST or not SMTP_USER:
        return
    body = (
        f"Hi,\n\n"
        f"A new dog has been reported on Pawfound that may match your dog \"{to_dog_name}\".\n\n"
        f"Match confidence: {round(similarity * 100)}%\n\n"
        f"View the potential match here:\n{APP_BASE_URL}/matches/{new_dog_id}\n\n"
        f"If this is your dog, please contact the reporter through the app.\n\n"
        f"– The Pawfound Team\n\n"
        f"(You received this because you have an active report on Pawfound. "
        f"To stop receiving these emails, mark your report as Reunited.)"
    )
    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"Possible match found for {to_dog_name} on Pawfound"
    msg["From"] = SMTP_FROM
    msg["To"] = to_email
    msg.attach(MIMEText(body, "plain"))
    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.ehlo()
            server.starttls()
            server.login(SMTP_USER, SMTP_PASS)
            server.sendmail(SMTP_FROM, [to_email], msg.as_string())
    except Exception:
        pass


def _notify_potential_matches(new_dog_id: str, new_dog_name: str, new_lost_or_found: str, embedding: list) -> None:
    """
    Called as a background task after every new report.
    Searches for visual matches of the opposite type (lost↔found) and notifies
    each matching dog's owner via an in-app system message and optional email.
    Deduplicates by dog_id so a dog with multiple photos only generates one notification.
    """
    # Search for the opposite type: a new lost report searches found dogs, and vice versa
    search_type = "found" if new_lost_or_found == "lost" else "lost"
    try:
        results = _collection.query(
            query_embeddings=[embedding],
            n_results=10,
            where={"lost_or_found": search_type},
            include=["metadatas", "distances"],
        )
    except Exception:
        return

    ids = results["ids"][0]
    distances = results["distances"][0]
    metadatas = results["metadatas"][0]

    db = SessionLocal()
    try:
        notified_dog_ids: set[str] = set()
        for chroma_id, distance, meta in zip(ids, distances, metadatas):
            # ChromaDB cosine distance: similarity = 1 - distance
            similarity = 1.0 - distance
            if similarity < NOTIFY_THRESHOLD:
                continue
            if meta.get("status") == "reunited":
                continue

            # Each photo has its own chroma entry; deduplicate notifications by dog_id
            matched_dog_id = meta.get("dog_id", "")
            if not matched_dog_id or matched_dog_id in notified_dog_ids:
                continue
            notified_dog_ids.add(matched_dog_id)

            # dog_id in Chroma metadata is a Postgres UUID string
            try:
                matched_dog = db.query(Dog).filter(Dog.id == uuid.UUID(matched_dog_id)).first()
            except (ValueError, AttributeError):
                matched_dog = db.query(Dog).filter(Dog.chroma_id == matched_dog_id).first()
            if not matched_dog:
                continue

            pct = round(similarity * 100)
            body = (
                f"🐾 AI Match Alert — {pct}% similarity\n\n"
                f"A new {new_lost_or_found} report for \"{new_dog_name}\" closely matches your dog \"{matched_dog.dog_name}\".\n\n"
                f"View the potential match: /browse/{new_dog_id}"
            )
            # sender_id=None marks this as a system message (rendered differently in the inbox UI)
            db.add(Message(
                sender_id=None,
                dog_id=matched_dog.id,
                body=body,
                is_system=True,
            ))

            contact_email = meta.get("contact_email", "")
            if contact_email:
                _send_match_email(contact_email, matched_dog.dog_name, new_dog_name, similarity, new_dog_id)

        db.commit()
    finally:
        db.close()


@app.post("/report")
async def report_dog(
    background_tasks: BackgroundTasks,
    images: list[UploadFile] = File(...),
    dog_name: str = Form("Unknown"),
    breed: str = Form(...),
    color: str = Form(""),
    age: str = Form(""),
    distinctive_markings: str = Form(""),
    location: str = Form(...),
    contact_email: str = Form(...),
    lost_or_found: str = Form(...),
    latitude: Optional[float] = Form(None),
    longitude: Optional[float] = Form(None),
    current_user: dict = Depends(get_current_user),
):
    if not images or len(images) > 5:
        raise HTTPException(status_code=422, detail="Provide between 1 and 5 images")

    dog_id = str(uuid.uuid4())
    primary_embedding: list | None = None

    db = SessionLocal()
    try:
        db_dog = Dog(
            id=uuid.UUID(dog_id),
            dog_name=dog_name,
            breed=breed,
            color=color,
            age=age,
            distinctive_markings=distinctive_markings,
            location=location,
            contact_email=contact_email,
            lost_or_found=lost_or_found,
            latitude=latitude,
            longitude=longitude,
            user_id=uuid.UUID(current_user["sub"]),
        )

        for idx, image in enumerate(images):
            image_bytes = await image.read()
            embedding = get_embedding(image_bytes)
            if idx == 0:
                primary_embedding = embedding

            photo_chroma_id = str(uuid.uuid4())
            image_b64 = base64.b64encode(image_bytes).decode("utf-8")

            meta: dict = {
                "dog_id": dog_id,
                "dog_name": dog_name,
                "breed": breed,
                "color": color,
                "age": age,
                "distinctive_markings": distinctive_markings,
                "location": location,
                "contact_email": contact_email,
                "lost_or_found": lost_or_found,
                "status": "active",
                "image_b64": image_b64,
                "content_type": image.content_type or "image/jpeg",
            }
            if latitude is not None:
                meta["latitude"] = latitude
            if longitude is not None:
                meta["longitude"] = longitude

            _collection.add(
                ids=[photo_chroma_id],
                embeddings=[embedding],
                metadatas=[meta],
            )

            if idx == 0:
                db_dog.chroma_id = photo_chroma_id

            db.add(DogPhoto(
                dog_id=uuid.UUID(dog_id),
                chroma_id=photo_chroma_id,
                is_primary=(idx == 0),
            ))

        db.add(db_dog)
        db.commit()
    finally:
        db.close()

    if primary_embedding:
        background_tasks.add_task(_notify_potential_matches, dog_id, dog_name, lost_or_found, primary_embedding)

    return {"dog_id": dog_id}


@app.post("/match")
async def match_dog(
    request: Request,
    image: UploadFile = File(...),
    exclude_id: Optional[str] = Form(None),
    lost_or_found: Optional[str] = Form(None),
    include_reunited: bool = Form(False),
    filter_lat: Optional[float] = Form(None),
    filter_lng: Optional[float] = Form(None),
    filter_radius_km: Optional[float] = Form(None),
):
    image_bytes = await image.read()
    embedding = get_embedding(image_bytes)

    where_filter = {"lost_or_found": lost_or_found} if lost_or_found else None

    results = _collection.query(
        query_embeddings=[embedding],
        n_results=25,
        where=where_filter,
        include=["metadatas", "distances"],
    )

    ids = results["ids"][0]
    distances = results["distances"][0]
    metadatas = results["metadatas"][0]

    # Deduplicate by dog_id, keeping best similarity per dog
    best: dict[str, dict] = {}
    for chroma_id, distance, meta in zip(ids, distances, metadatas):
        dog_id = meta.get("dog_id", chroma_id)
        if exclude_id and dog_id == exclude_id:
            continue
        similarity = 1.0 - distance
        if similarity < SIMILARITY_THRESHOLD:
            continue
        if not include_reunited and meta.get("status") == "reunited":
            continue
        if dog_id not in best or similarity > best[dog_id]["similarity"]:
            best[dog_id] = {"similarity": similarity, "meta": dict(meta), "chroma_id": chroma_id}

    geo_filter = filter_lat is not None and filter_lng is not None and filter_radius_km is not None

    matches = []
    for dog_id, entry in sorted(best.items(), key=lambda x: x[1]["similarity"], reverse=True):
        meta = entry["meta"]

        # Geo filter: dogs with no coords pass through
        if geo_filter:
            lat = meta.get("latitude")
            lng = meta.get("longitude")
            if lat is not None and lng is not None:
                if _haversine_km(filter_lat, filter_lng, lat, lng) > filter_radius_km:
                    continue

        meta.pop("image_b64", None)
        meta.pop("content_type", None)
        chroma_id = entry["chroma_id"]

        matches.append({
            "dog_id": dog_id,
            "similarity": round(entry["similarity"], 4),
            "metadata": meta,
            "image": _image_url(request, chroma_id),
        })

    return {"matches": matches[:5]}


@app.get("/dogs")
async def list_dogs(
    request: Request,
    limit: int = 20,
    offset: int = 0,
    lat: Optional[float] = None,
    lng: Optional[float] = None,
    radius_km: Optional[float] = None,
):
    """Return a paginated list of all reported dogs (newest first via Postgres)."""
    db = SessionLocal()
    try:
        rows = (
            db.query(Dog)
            .order_by(Dog.created_at.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )
    finally:
        db.close()

    geo_filter = lat is not None and lng is not None and radius_km is not None
    if geo_filter:
        rows = [
            r for r in rows
            if r.latitude is None or r.longitude is None
            or _haversine_km(lat, lng, r.latitude, r.longitude) <= radius_km
        ]

    dogs = []
    for row in rows:
        result = _collection.get(ids=[row.chroma_id], include=["metadatas"])
        if not result["ids"]:
            continue
        meta = dict(result["metadatas"][0])
        meta.pop("image_b64", None)
        meta.pop("content_type", None)
        dogs.append({
            "dog_id": row.chroma_id,
            "metadata": meta,
            "status": row.status,
            "latitude": row.latitude,
            "longitude": row.longitude,
            "image": _image_url(request, row.chroma_id) if row.chroma_id else None,
        })

    return {"dogs": dogs}


@app.get("/dog/{dog_id}")
async def get_dog(dog_id: str):
    db = SessionLocal()
    try:
        # Dogs are referenced by Postgres UUID from /report and by chroma_id from /dogs.
        # Accept both so that navigation from the browse feed and from report success both work.
        db_dog = None
        try:
            db_dog = db.query(Dog).filter(Dog.id == uuid.UUID(dog_id)).first()
        except (ValueError, AttributeError):
            pass
        if not db_dog:
            db_dog = db.query(Dog).filter(Dog.chroma_id == dog_id).first()
        if not db_dog:
            raise HTTPException(status_code=404, detail="Dog not found")

        status = db_dog.status
        latitude = db_dog.latitude
        longitude = db_dog.longitude

        # Build metadata from DB
        meta = {
            "dog_name": db_dog.dog_name,
            "breed": db_dog.breed,
            "color": db_dog.color,
            "age": db_dog.age,
            "distinctive_markings": db_dog.distinctive_markings,
            "location": db_dog.location,
            "contact_email": db_dog.contact_email,
            "lost_or_found": db_dog.lost_or_found,
            "status": status,
        }
        if latitude is not None:
            meta["latitude"] = latitude
        if longitude is not None:
            meta["longitude"] = longitude

        # Fetch all photos ordered primary first
        photos = (
            db.query(DogPhoto)
            .filter(DogPhoto.dog_id == db_dog.id)
            .order_by(DogPhoto.is_primary.desc(), DogPhoto.created_at)
            .all()
        )
    finally:
        db.close()

    images = []
    primary_image = None
    for photo in photos:
        pr = _collection.get(ids=[photo.chroma_id], include=["metadatas"])
        if pr["ids"]:
            pm = pr["metadatas"][0]
            pb64 = pm.get("image_b64")
            pct = pm.get("content_type", "image/jpeg")
            if pb64:
                data_uri = f"data:{pct};base64,{pb64}"
                images.append(data_uri)
                if photo.is_primary:
                    primary_image = data_uri

    return {
        "dog_id": dog_id,
        "chroma_id": db_dog.chroma_id,
        "metadata": meta,
        "status": status,
        "latitude": latitude,
        "longitude": longitude,
        "image": primary_image,
        "images": images,
    }


@app.patch("/dog/{dog_id}/status")
async def update_dog_status(
    dog_id: str,
    status: str = Form(...),
    current_user: dict = Depends(get_current_user),
):
    if status not in ("active", "reunited"):
        raise HTTPException(status_code=422, detail="status must be 'active' or 'reunited'")

    db = SessionLocal()
    try:
        dog = db.query(Dog).filter(Dog.chroma_id == dog_id).first()
        if not dog:
            raise HTTPException(status_code=404, detail="Dog not found")
        if dog.user_id != uuid.UUID(current_user["sub"]):
            raise HTTPException(status_code=403, detail="Not your dog")
        dog.status = status
        db.commit()
    finally:
        db.close()

    # Update all Chroma entries for this dog
    db2 = SessionLocal()
    try:
        db_dog = db2.query(Dog).filter(Dog.chroma_id == dog_id).first()
        if db_dog:
            photos = db2.query(DogPhoto).filter(DogPhoto.dog_id == db_dog.id).all()
            chroma_ids = [p.chroma_id for p in photos] or [dog_id]
            for cid in chroma_ids:
                pr = _collection.get(ids=[cid], include=["metadatas"])
                if pr["ids"]:
                    updated_meta = dict(pr["metadatas"][0])
                    updated_meta["status"] = status
                    _collection.update(ids=[cid], metadatas=[updated_meta])
    finally:
        db2.close()

    return {"dog_id": dog_id, "status": status}


@app.get("/users/me/dogs")
async def get_my_dogs(request: Request, current_user: dict = Depends(get_current_user)):
    """Return all dogs reported by the currently logged-in user."""
    user_uuid = uuid.UUID(current_user["sub"])
    db = SessionLocal()
    try:
        rows = (
            db.query(Dog)
            .filter(Dog.user_id == user_uuid)
            .order_by(Dog.created_at.desc())
            .all()
        )
    finally:
        db.close()

    dogs = []
    for row in rows:
        if not row.chroma_id:
            continue
        result = _collection.get(ids=[row.chroma_id], include=["metadatas"])
        if not result["ids"]:
            continue
        meta = dict(result["metadatas"][0])
        meta.pop("image_b64", None)
        meta.pop("content_type", None)
        dogs.append({
            "dog_id": row.chroma_id,
            "metadata": meta,
            "status": row.status,
            "latitude": row.latitude,
            "longitude": row.longitude,
            "image": _image_url(request, row.chroma_id),
            "created_at": row.created_at.isoformat() if row.created_at else None,
        })

    return {"dogs": dogs}


@app.post("/messages", status_code=201)
async def send_message(
    dog_id: str = Form(...),
    body: str = Form(...),
    current_user: dict = Depends(get_current_user),
):
    body = body.strip()
    if not body:
        raise HTTPException(status_code=422, detail="Message body cannot be empty")
    if len(body) > 2000:
        raise HTTPException(status_code=422, detail="Message body too long (max 2000 chars)")

    user_uuid = uuid.UUID(current_user["sub"])
    db = SessionLocal()
    try:
        dog = db.query(Dog).filter(Dog.chroma_id == dog_id).first()
        if not dog:
            raise HTTPException(status_code=404, detail="Dog not found")
        if dog.user_id == user_uuid:
            raise HTTPException(status_code=400, detail="You cannot message yourself")

        msg = Message(sender_id=user_uuid, dog_id=dog.id, body=body)
        db.add(msg)
        db.commit()
        db.refresh(msg)
        return {"message_id": str(msg.id), "created_at": msg.created_at.isoformat()}
    finally:
        db.close()


@app.get("/messages/inbox")
async def get_inbox(current_user: dict = Depends(get_current_user)):
    user_uuid = uuid.UUID(current_user["sub"])
    db = SessionLocal()
    try:
        my_dogs = db.query(Dog).filter(Dog.user_id == user_uuid).all()
        my_dog_ids = [d.id for d in my_dogs]
        dog_name_map = {d.id: d.dog_name for d in my_dogs}
        dog_chroma_map = {d.id: d.chroma_id for d in my_dogs}

        if not my_dog_ids:
            return {"threads": []}

        messages = (
            db.query(Message)
            .filter(Message.dog_id.in_(my_dog_ids))
            .order_by(Message.created_at.desc())
            .all()
        )

        # Group into threads by dog_id
        threads: dict[str, dict] = {}
        for msg in messages:
            key = str(msg.dog_id)
            if key not in threads:
                if msg.is_system:
                    sender_name = "Pawfound"
                else:
                    sender = db.query(User).filter(User.id == msg.sender_id).first()
                    sender_name = sender.name if sender else "Unknown"
                threads[key] = {
                    "dog_id_key": key,
                    "dog_name": dog_name_map.get(msg.dog_id, "Unknown"),
                    "unread_count": 0,
                    "latest_message": msg.body[:100],
                    "latest_at": msg.created_at.isoformat(),
                    "sender_name": sender_name,
                }
            if not msg.read:
                threads[key]["unread_count"] += 1

        result = []
        for key, t in threads.items():
            postgres_uuid = uuid.UUID(key)
            chroma_id = dog_chroma_map.get(postgres_uuid, key)
            result.append({
                "dog_id": chroma_id,
                "dog_name": t["dog_name"],
                "unread_count": t["unread_count"],
                "latest_message": t["latest_message"],
                "latest_at": t["latest_at"],
                "sender_name": t["sender_name"],
            })

        return {"threads": result}
    finally:
        db.close()


@app.get("/messages/thread/{dog_id}")
async def get_thread(dog_id: str, current_user: dict = Depends(get_current_user)):
    user_uuid = uuid.UUID(current_user["sub"])
    db = SessionLocal()
    try:
        dog = db.query(Dog).filter(Dog.chroma_id == dog_id).first()
        if not dog:
            raise HTTPException(status_code=404, detail="Dog not found")

        is_owner = dog.user_id == user_uuid
        messages = (
            db.query(Message)
            .filter(Message.dog_id == dog.id)
            .order_by(Message.created_at.asc())
            .all()
        )

        # Only owners see threads; senders can only see if they have messages here
        if not is_owner:
            sender_msgs = [m for m in messages if m.sender_id == user_uuid]
            if not sender_msgs:
                raise HTTPException(status_code=403, detail="Not authorized")

        result = []
        for msg in messages:
            if msg.is_system:
                sender_name = "Pawfound"
                sender_id_str = "system"
                is_mine = False
            else:
                sender = db.query(User).filter(User.id == msg.sender_id).first()
                sender_name = sender.name if sender else "Unknown"
                sender_id_str = str(msg.sender_id)
                is_mine = msg.sender_id == user_uuid
            result.append({
                "message_id": str(msg.id),
                "sender_id": sender_id_str,
                "sender_name": sender_name,
                "body": msg.body,
                "created_at": msg.created_at.isoformat(),
                "read": msg.read,
                "is_system": msg.is_system,
                "is_mine": is_mine,
            })
            # Mark unread messages as read if current user is owner
            if is_owner and not msg.read:
                msg.read = True

        db.commit()
        return {"messages": result, "dog_name": dog.dog_name}
    finally:
        db.close()


@app.get("/messages/unread-count")
async def get_unread_count(current_user: dict = Depends(get_current_user)):
    user_uuid = uuid.UUID(current_user["sub"])
    db = SessionLocal()
    try:
        my_dog_ids = [d.id for d in db.query(Dog).filter(Dog.user_id == user_uuid).all()]
        if not my_dog_ids:
            return {"unread": 0}
        count = db.query(Message).filter(
            Message.dog_id.in_(my_dog_ids),
            Message.read == False,
        ).count()
        return {"unread": count}
    finally:
        db.close()

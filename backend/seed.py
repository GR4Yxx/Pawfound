"""
Seed the Pawfound database with sample data.

Creates one test user and 30 dogs from the Stanford Dogs dataset images.

Usage:
    python seed.py          # inside backend container (make seed)
"""

import argparse
import base64
import os
import sys
import uuid
from pathlib import Path

IMAGES_DIR = Path(__file__).parent.parent / "trainer" / "data" / "Images"

# (breed_folder, filename, dog_name, color, age, markings, location, lost_or_found)
_DOGS_RAW = [
    # Chihuahua x2
    ("n02085620-Chihuahua",      "n02085620_10074.jpg", "Taco",    "Tan",          "Young",  "Very small, large ears",                  "Los Angeles, CA",  "lost"),
    ("n02085620-Chihuahua",      "n02085620_10131.jpg", "Taco",    "Tan",          "Young",  "Very small, large ears",                  "Los Angeles, CA",  "found"),
    # Beagle x2
    ("n02088364-beagle",         "n02088364_10108.jpg", "Cooper",  "Tricolor",     "Adult",  "Tricolor coat, white-tipped tail",        "Chicago, IL",      "lost"),
    ("n02088364-beagle",         "n02088364_10206.jpg", "Cooper",  "Tricolor",     "Adult",  "Tricolor coat, white-tipped tail",        "Chicago, IL",      "found"),
    # Shih-Tzu x2
    ("n02086240-Shih-Tzu",       "n02086240_1011.jpg",  "Mochi",   "White & Brown","Senior", "Long silky coat, bow in hair",            "Seattle, WA",      "lost"),
    ("n02086240-Shih-Tzu",       "n02086240_1016.jpg",  "Mochi",   "White & Brown","Senior", "Long silky coat, bow in hair",            "Seattle, WA",      "found"),
    # Walker Hound x2
    ("n02089867-Walker_hound",   "n02089867_1029.jpg",  "Duke",    "Tricolor",     "Adult",  "Broad white blaze on face",               "Nashville, TN",    "lost"),
    ("n02089867-Walker_hound",   "n02089867_1048.jpg",  "Rex",     "Brown & White","Adult",  "Spotted back, long tail",                 "Memphis, TN",      "lost"),
    # Bedlington Terrier x2
    ("n02093647-Bedlington_terrier","n02093647_1022.jpg","Archie", "Grey",         "Young",  "Lamb-like fluffy coat, tufted head",      "Portland, OR",     "lost"),
    ("n02093647-Bedlington_terrier","n02093647_1030.jpg","Archie", "Grey",         "Young",  "Lamb-like fluffy coat, tufted head",      "Portland, OR",     "found"),
    # Yorkshire Terrier x2
    ("n02094433-Yorkshire_terrier","n02094433_10123.jpg","Penny",  "Tan & Blue",   "Adult",  "Silky long coat, small bow",              "New York, NY",     "lost"),
    ("n02094433-Yorkshire_terrier","n02094433_10126.jpg","Penny",  "Tan & Blue",   "Adult",  "Silky long coat, small bow",              "New York, NY",     "found"),
    # Golden Retriever x3
    ("n02099601-golden_retriever","n02099601_10.jpg",    "Jade",   "Golden",       "Adult",  "Fluffy coat, white patch on chest",       "Brooklyn, NY",     "lost"),
    ("n02099601-golden_retriever","n02099601_100.jpg",   "Jade",   "Golden",       "Adult",  "Fluffy coat, white patch on chest",       "Brooklyn, NY",     "found"),
    ("n02099601-golden_retriever","n02099601_1010.jpg",  "Sunny",  "Light Golden", "Puppy",  "Very light coat, floppy ears",            "Queens, NY",       "lost"),
    # Vizsla x2
    ("n02100583-vizsla",         "n02100583_10249.jpg", "Rusty",   "Rust",         "Adult",  "Sleek rust coat, no markings",            "Denver, CO",       "lost"),
    ("n02100583-vizsla",         "n02100583_10358.jpg", "Rusty",   "Rust",         "Adult",  "Sleek rust coat, no markings",            "Denver, CO",       "found"),
    # Rottweiler x2
    ("n02106550-Rottweiler",     "n02106550_10048.jpg", "Bruno",   "Black & Tan",  "Adult",  "Tan eyebrow markings, thick neck",        "Houston, TX",      "lost"),
    ("n02106550-Rottweiler",     "n02106550_10222.jpg", "Bruno",   "Black & Tan",  "Adult",  "Tan eyebrow markings, thick neck",        "Houston, TX",      "found"),
    # French Bulldog x2
    ("n02108915-French_bulldog", "n02108915_10204.jpg", "Gus",     "Brindle",      "Adult",  "Bat ears, brindle coat, curly tail",      "Miami, FL",        "lost"),
    ("n02108915-French_bulldog", "n02108915_10564.jpg", "Gus",     "Brindle",      "Adult",  "Bat ears, brindle coat, curly tail",      "Miami, FL",        "found"),
    # Pug x2
    ("n02110958-pug",            "n02110958_10.jpg",    "Otto",    "Fawn",         "Adult",  "Curly tail, black mask on face",          "Phoenix, AZ",      "lost"),
    ("n02110958-pug",            "n02110958_10186.jpg", "Otto",    "Fawn",         "Adult",  "Curly tail, black mask on face",          "Phoenix, AZ",      "found"),
    # Pembroke Corgi x2
    ("n02113023-Pembroke",       "n02113023_10636.jpg", "Beans",   "Sable & White","Young",  "Short legs, fox-like face, no tail",      "San Diego, CA",    "lost"),
    ("n02113023-Pembroke",       "n02113023_10829.jpg", "Beans",   "Sable & White","Young",  "Short legs, fox-like face, no tail",      "San Diego, CA",    "found"),
    # Australian Terrier x1
    ("n02096294-Australian_terrier","n02096294_1111.jpg","Digger", "Tan & Blue",   "Adult",  "Rough wiry coat, topknot on head",        "Austin, TX",       "lost"),
    # Groenendael x1
    ("n02105056-groenendael",    "n02105056_1018.jpg",  "Shadow",  "Black",        "Adult",  "Thick all-black double coat",             "Boston, MA",       "lost"),
    # Eskimo Dog x2
    ("n02109961-Eskimo_dog",     "n02109961_10021.jpg", "Blizzard","White",        "Adult",  "Thick white double coat, curled tail",    "Minneapolis, MN",  "lost"),
    ("n02109961-Eskimo_dog",     "n02109961_1017.jpg",  "Blizzard","White",        "Adult",  "Thick white double coat, curled tail",    "Minneapolis, MN",  "found"),
]

# Build SEED_DOGS list
SEED_DOGS = []
for folder, filename, dog_name, color, age, markings, location, status in _DOGS_RAW:
    breed = folder.split("-", 1)[1].replace("_", " ").title()
    SEED_DOGS.append({
        "image_path": IMAGES_DIR / folder / filename,
        "fields": {
            "dog_name": dog_name,
            "breed": breed,
            "color": color,
            "age": age,
            "distinctive_markings": markings,
            "location": location,
            "contact_email": f"{dog_name.lower()}-{'owner' if status == 'lost' else 'finder'}@example.com",
            "lost_or_found": status,
        },
    })

TEST_USER = {
    "email": "demo@pawfound.app",
    "password": "demo1234",
    "name": "Demo User",
}


def seed() -> None:
    """Insert test user + seed dogs directly into PostgreSQL + ChromaDB."""
    import chromadb
    from dotenv import load_dotenv

    load_dotenv()

    from database import Dog, DogPhoto, SessionLocal, User, init_db
    from embedder import get_embedding
    from passlib.context import CryptContext

    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

    chroma_path = os.getenv("CHROMA_PATH", "/chroma_data")
    client = chromadb.PersistentClient(path=chroma_path)
    collection = client.get_or_create_collection(
        name="dogs",
        metadata={"hnsw:space": "cosine"},
    )

    init_db()
    db = SessionLocal()

    # ── Create test user ──────────────────────────────────────────────────────
    existing = db.query(User).filter(User.email == TEST_USER["email"]).first()
    if existing:
        print(f"  SKIP  user {TEST_USER['email']} — already exists")
        test_user_id = existing.id
    else:
        user = User(
            email=TEST_USER["email"],
            name=TEST_USER["name"],
            password_hash=pwd_context.hash(TEST_USER["password"]),
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        test_user_id = user.id
        print(f"  OK    user {TEST_USER['email']} created (id: {test_user_id})")

    # ── Seed dogs ─────────────────────────────────────────────────────────────
    print(f"\nSeeding {len(SEED_DOGS)} dogs → PostgreSQL + ChromaDB\n")

    ok = 0
    try:
        for entry in SEED_DOGS:
            image_path: Path = entry["image_path"]
            fields: dict = entry["fields"]

            if not image_path.exists():
                print(f"  SKIP  {image_path.name} — file not found")
                continue

            image_bytes = image_path.read_bytes()
            content_type = "image/jpeg" if image_path.suffix.lower() in (".jpg", ".jpeg") else "image/png"
            image_b64 = base64.b64encode(image_bytes).decode("utf-8")

            try:
                embedding = get_embedding(image_bytes)
            except Exception as exc:
                print(f"  ERROR {image_path.name} → embedding failed: {exc}")
                continue

            dog_id = str(uuid.uuid4())

            collection.add(
                ids=[dog_id],
                embeddings=[embedding],
                metadatas=[{
                    **fields,
                    "dog_id": dog_id,
                    "status": "active",
                    "image_b64": image_b64,
                    "content_type": content_type,
                }],
            )

            db.add(Dog(
                id=uuid.UUID(dog_id),
                dog_name=fields["dog_name"],
                breed=fields["breed"],
                color=fields["color"],
                age=fields["age"],
                distinctive_markings=fields["distinctive_markings"],
                location=fields["location"],
                contact_email=fields["contact_email"],
                lost_or_found=fields["lost_or_found"],
                chroma_id=dog_id,
                user_id=test_user_id,
            ))
            db.add(DogPhoto(
                dog_id=uuid.UUID(dog_id),
                chroma_id=dog_id,
                is_primary=True,
            ))
            db.commit()

            print(f"  OK    {image_path.name} → {fields['dog_name']} ({fields['lost_or_found']})")
            ok += 1
    except Exception as exc:
        db.rollback()
        print(f"\n  FATAL {exc}", file=sys.stderr)
        sys.exit(1)
    finally:
        db.close()

    print(f"\nDone — {ok}/{len(SEED_DOGS)} dogs seeded.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed the Pawfound database.")
    parser.add_argument("--url", default=None, help="Ignored — kept for backwards compat.")
    parser.parse_args()
    seed()

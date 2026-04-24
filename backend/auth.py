"""
Lightweight email + password auth for Pawfound.

Routes:
  POST /auth/register  — create account, set JWT cookie
  POST /auth/login     — verify password, set JWT cookie
  GET  /auth/me        — return current user from JWT cookie (401 if absent/invalid)
  POST /auth/logout    — clear JWT cookie
"""

import os
from datetime import datetime, timedelta, timezone

from dotenv import load_dotenv
from fastapi import APIRouter, Cookie, HTTPException
from fastapi.responses import JSONResponse
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel, EmailStr

from database import SessionLocal, User

load_dotenv()

JWT_SECRET = os.getenv("JWT_SECRET", "change-me-in-production")
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_DAYS = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
router = APIRouter(prefix="/auth", tags=["auth"])


# ── Pydantic schemas ──────────────────────────────────────────────────────────

class RegisterBody(BaseModel):
    email: EmailStr
    name: str
    password: str


class LoginBody(BaseModel):
    email: EmailStr
    password: str


# ── Helpers ───────────────────────────────────────────────────────────────────

def _hash_password(plain: str) -> str:
    return pwd_context.hash(plain)


def _verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def _create_jwt(user_id: str, email: str, name: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(days=JWT_EXPIRE_DAYS)
    return jwt.encode(
        {"sub": user_id, "email": email, "name": name, "exp": expire},
        JWT_SECRET,
        algorithm=JWT_ALGORITHM,
    )


def _decode_jwt(token: str) -> dict:
    return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])


def _set_cookie(response: JSONResponse, token: str) -> None:
    response.set_cookie(
        key="auth_token",
        value=token,
        httponly=True,
        samesite="lax",
        secure=False,   # set True in production behind HTTPS
        max_age=60 * 60 * 24 * JWT_EXPIRE_DAYS,
        path="/",
    )


def _user_json(user: User) -> dict:
    return {
        "id": str(user.id),
        "email": user.email,
        "name": user.name,
        "picture": user.picture,
    }


# ── Routes ────────────────────────────────────────────────────────────────────

@router.post("/register", status_code=201)
def register(body: RegisterBody):
    """Create a new account and return a JWT cookie."""
    if len(body.password) < 8:
        raise HTTPException(status_code=422, detail="Password must be at least 8 characters.")

    db = SessionLocal()
    try:
        if db.query(User).filter(User.email == body.email).first():
            raise HTTPException(status_code=409, detail="An account with this email already exists.")

        user = User(
            email=body.email,
            name=body.name.strip() or body.email.split("@")[0],
            password_hash=_hash_password(body.password),
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        token = _create_jwt(str(user.id), user.email, user.name)
        response = JSONResponse(content=_user_json(user), status_code=201)
        _set_cookie(response, token)
        return response
    finally:
        db.close()


@router.post("/login")
def login(body: LoginBody):
    """Verify credentials and return a JWT cookie."""
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == body.email).first()
        if not user or not _verify_password(body.password, user.password_hash):
            raise HTTPException(status_code=401, detail="Invalid email or password.")

        token = _create_jwt(str(user.id), user.email, user.name)
        response = JSONResponse(content=_user_json(user))
        _set_cookie(response, token)
        return response
    finally:
        db.close()


@router.get("/me")
def get_me(auth_token: str | None = Cookie(default=None)):
    """Return the current user from the JWT cookie, or 401."""
    if not auth_token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        payload = _decode_jwt(auth_token)
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    return {
        "id": payload["sub"],
        "email": payload["email"],
        "name": payload["name"],
        "picture": payload.get("picture"),
    }


@router.post("/logout")
def logout():
    """Clear the JWT cookie."""
    response = JSONResponse(content={"ok": True})
    response.delete_cookie(key="auth_token", path="/")
    return response


# ── Dependency ────────────────────────────────────────────────────────────────

def get_current_user(auth_token: str | None = Cookie(default=None)) -> dict:
    """
    FastAPI dependency — validates JWT cookie and returns user payload.
    Raises 401 if the cookie is missing or invalid.
    """
    if not auth_token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        payload = _decode_jwt(auth_token)
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return payload

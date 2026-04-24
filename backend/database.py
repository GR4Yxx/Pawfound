import os
import uuid
from datetime import datetime, timezone

from dotenv import load_dotenv
from sqlalchemy import (
    Boolean, Column, DateTime, Float, ForeignKey, String, Text, create_engine
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, relationship, sessionmaker

load_dotenv()

_DB_URL = os.getenv("DB_URL", "")

engine = create_engine(_DB_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), nullable=False, unique=True)
    name = Column(String(255), nullable=False, default="")
    password_hash = Column(Text, nullable=False)
    picture = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    dogs = relationship("Dog", back_populates="user")


class Dog(Base):
    __tablename__ = "dogs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    dog_name = Column(String(255), nullable=False, default="")
    breed = Column(String(255), nullable=False, default="")
    color = Column(String(255), nullable=False, default="")
    age = Column(String(100), nullable=False, default="")
    distinctive_markings = Column(Text, nullable=False, default="")
    location = Column(String(255), nullable=False, default="")
    contact_email = Column(String(255), nullable=False, default="")
    lost_or_found = Column(String(10), nullable=False, default="lost")
    status = Column(String(20), nullable=False, default="active")
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    image_path = Column(Text, nullable=True)
    chroma_id = Column(String(36), nullable=True, unique=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)

    user = relationship("User", back_populates="dogs")
    photos = relationship("DogPhoto", back_populates="dog", order_by="DogPhoto.created_at")


class DogPhoto(Base):
    __tablename__ = "dog_photos"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    dog_id = Column(UUID(as_uuid=True), ForeignKey("dogs.id"), nullable=False)
    chroma_id = Column(String(36), nullable=False, unique=True)
    is_primary = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    dog = relationship("Dog", back_populates="photos")


class Message(Base):
    __tablename__ = "messages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    sender_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    dog_id = Column(UUID(as_uuid=True), ForeignKey("dogs.id"), nullable=False)
    body = Column(Text, nullable=False)
    image_b64 = Column(Text, nullable=True)
    image_content_type = Column(String(50), nullable=True)
    read = Column(Boolean, nullable=False, default=False)
    is_system = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    sender = relationship("User", foreign_keys=[sender_id])
    dog = relationship("Dog")


def init_db() -> None:
    """Create all tables if they don't already exist."""
    Base.metadata.create_all(bind=engine)

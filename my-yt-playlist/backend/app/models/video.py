import uuid
from datetime import datetime
from typing import TYPE_CHECKING, List, Optional
from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.collection import Collection
    from app.models.tag import Tag
    from app.models.user import User


class Video(Base, TimestampMixin):
    """Global YouTube video metadata cached entity."""

    __tablename__ = "videos"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    youtube_video_id: Mapped[str] = mapped_column(
        String(20),
        unique=True,
        index=True,
        nullable=False,
    )
    youtube_url: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )
    title: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    channel_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    channel_id: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    thumbnail_url: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
    )
    duration_seconds: Mapped[int] = mapped_column(
        Integer,
        index=True,
        nullable=False,
    )
    published_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    category_id: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
    )
    is_unavailable: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )
    fetched_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    user_videos: Mapped[List["UserVideo"]] = relationship(
        "UserVideo",
        back_populates="video",
        cascade="all, delete-orphan",
    )


class UserVideo(Base):
    """User-specific video saved state entity."""

    __tablename__ = "user_videos"
    __table_args__ = (
        UniqueConstraint("user_id", "video_id", name="uq_user_video"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    video_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("videos.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    status: Mapped[str] = mapped_column(
        String(20),
        default="unwatched",
        nullable=False,
    )
    is_favourite: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        index=True,
        nullable=False,
    )
    is_watch_later: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        index=True,
        nullable=False,
    )
    user_category: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
    )
    notes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    added_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        index=True,
        nullable=False,
    )
    watched_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    user: Mapped["User"] = relationship(
        "User",
        back_populates="user_videos",
    )
    video: Mapped["Video"] = relationship(
        "Video",
        back_populates="user_videos",
    )
    timestamp_notes: Mapped[List["TimestampNote"]] = relationship(
        "TimestampNote",
        back_populates="user_video",
        cascade="all, delete-orphan",
    )
    collections: Mapped[List["Collection"]] = relationship(
        "Collection",
        secondary="collection_videos",
        back_populates="user_videos",
    )
    tags: Mapped[List["Tag"]] = relationship(
        "Tag",
        secondary="user_video_tags",
        back_populates="user_videos",
    )


class TimestampNote(Base):
    """Timestamped note associated with a UserVideo."""

    __tablename__ = "timestamp_notes"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    user_video_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("user_videos.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    timestamp_seconds: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    note_text: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationship
    user_video: Mapped["UserVideo"] = relationship(
        "UserVideo",
        back_populates="timestamp_notes",
    )

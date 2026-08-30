"""
Import all ORM models here so that Alembic can auto-detect
metadata changes across the entire application domain.
"""
from app.models.base import Base
from app.models.collection import Collection, CollectionVideo
from app.models.tag import Tag, UserVideoTag
from app.models.user import RefreshToken, User
from app.models.video import TimestampNote, UserVideo, Video

__all__ = ["Base"]

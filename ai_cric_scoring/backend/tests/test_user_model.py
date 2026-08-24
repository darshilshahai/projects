import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError
from app.models.user import User
from app.schemas.user import UserPublic
from app.services.user import UserService


@pytest.mark.asyncio
async def test_user_can_be_inserted(db_session: AsyncSession, user: User) -> None:
    assert user.id is not None
    assert user.email == "owner@example.com"
    assert user.password_hash == "not-a-real-hash"
    assert user.is_active is True
    loaded = await UserService(db_session).get_by_id(user.id)
    assert loaded.email == user.email


@pytest.mark.asyncio
async def test_duplicate_email_is_rejected(db_session: AsyncSession, user: User) -> None:
    service = UserService(db_session)
    with pytest.raises(ConflictError):
        await service.create(email="owner@example.com", password_hash="other-hash")


@pytest.mark.asyncio
async def test_duplicate_email_is_case_insensitive(db_session: AsyncSession, user: User) -> None:
    service = UserService(db_session)
    with pytest.raises(ConflictError):
        await service.create(email="Owner@Example.com", password_hash="other-hash")


@pytest.mark.asyncio
async def test_user_public_schema_excludes_password_hash(user: User) -> None:
    public = UserPublic.model_validate(user)
    assert public.email == user.email
    assert "password_hash" not in public.model_dump()

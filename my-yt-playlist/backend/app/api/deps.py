from uuid import UUID
from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import settings
from app.core.exceptions import InactiveUserException, InvalidTokenException
from app.core.security import decode_token
from app.db.session import get_db
from app.models.user import User
from app.repositories.user_repository import UserRepository

# OAuth2 Scheme for Bearer Authorization header extraction
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/auth/login"
)


async def get_current_user(
    db: AsyncSession = Depends(get_db), token: str = Depends(oauth2_scheme)
) -> User:
    """
    Dependency that validates JWT Access Token and retrieves authenticated User.
    Enforces user authentication across protected API endpoints.
    """
    try:
        payload = decode_token(token)
    except Exception:
        raise InvalidTokenException()

    if payload.get("type") != "access":
        raise InvalidTokenException("Token is not a valid access token.")

    user_id_str: str = payload.get("sub", "")
    if not user_id_str:
        raise InvalidTokenException()

    try:
        user_id = UUID(user_id_str)
    except ValueError:
        raise InvalidTokenException()

    user_repo = UserRepository(db)
    user = await user_repo.get_by_id(user_id)
    if not user:
        raise InvalidTokenException("User no longer exists.")

    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """Dependency enforcing that current user account is active."""
    if not current_user.is_active:
        raise InactiveUserException()
    return current_user

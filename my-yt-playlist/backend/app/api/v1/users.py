from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_current_active_user, get_db
from app.core.exceptions import InvalidCredentialsException
from app.core.security import get_password_hash, verify_password
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.user import PasswordChangeRequest, UserResponse, UserUpdateRequest

router = APIRouter()


@router.get(
    "/me",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Get current user profile",
)
async def get_my_profile(
    current_user: User = Depends(get_current_active_user),
):
    """Retrieve profile details of currently authenticated user."""
    return current_user


@router.patch(
    "/me",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Update current user profile",
)
async def update_my_profile(
    data: UserUpdateRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Update profile information (e.g. full name) for current user."""
    repo = UserRepository(db)
    updated_user = await repo.update_user(
        current_user, data.model_dump(exclude_unset=True)
    )
    return updated_user


@router.post(
    "/me/change-password",
    status_code=status.HTTP_200_OK,
    summary="Change account password",
)
async def change_password(
    data: PasswordChangeRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Change user account password.
    Verifies current password before updating to new Argon2id hash.
    """
    if not verify_password(data.current_password, current_user.hashed_password):
        raise InvalidCredentialsException("Current password is incorrect.")

    new_hash = get_password_hash(data.new_password)
    repo = UserRepository(db)
    await repo.update_user(current_user, {"hashed_password": new_hash})
    return {"message": "Password successfully updated."}

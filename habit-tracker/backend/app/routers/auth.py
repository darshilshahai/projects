from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from supabase import Client

from app.db.supabase import get_anon_client, get_service_client
from app.deps import CurrentUser, get_current_user
from app.schemas.auth import (
    AuthSessionOut,
    SignInRequest,
    SignUpRequest,
    UserOut,
)

router = APIRouter(prefix="/auth", tags=["auth"])


def _session_response(session, user) -> AuthSessionOut:
    if session is None or user is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Authentication failed",
        )
    return AuthSessionOut(
        accessToken=session.access_token,
        refreshToken=session.refresh_token,
        expiresIn=session.expires_in,
        tokenType=session.token_type or "bearer",
        user=UserOut(id=str(user.id), email=user.email),
    )


def _auth_error_detail(exc: Exception) -> str:
    message = str(exc)
    # Prefer AuthApiError fields when present
    detail = getattr(exc, "message", None) or message
    code = getattr(exc, "code", None) or getattr(exc, "error_code", None)
    if code == "email_address_invalid" or "is invalid" in detail.lower():
        return (
            f"{detail}. Tip: disable Confirm email in Supabase "
            "(Authentication → Providers → Email), or use a real inbox you own."
        )
    if code == "email_address_not_authorized":
        return (
            "This email cannot receive mail via Supabase's default SMTP. "
            "Use your Supabase org email, disable Confirm email, or add custom SMTP."
        )
    if code == "user_already_exists" or "already been registered" in detail.lower():
        return "An account with this email already exists. Sign in instead."
    return detail


@router.post("/signup", response_model=AuthSessionOut)
def signup(body: SignUpRequest):
    """
    Create a confirmed user via the service-role admin API, then sign in.

    This avoids Supabase default-SMTP / email-validity checks that often reject
    signups during local development when "Confirm email" is enabled.
    """
    email = str(body.email).strip().lower()
    password = body.password
    service: Client = get_service_client()

    try:
        created = service.auth.admin.create_user(
            {
                "email": email,
                "password": password,
                "email_confirm": True,
            }
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=_auth_error_detail(exc),
        ) from exc

    if created.user is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Sign up failed",
        )

    anon: Client = get_anon_client()
    try:
        result = anon.auth.sign_in_with_password(
            {"email": email, "password": password}
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "User was created but sign-in failed. "
                f"{_auth_error_detail(exc)}"
            ),
        ) from exc

    return _session_response(result.session, result.user)


@router.post("/signin", response_model=AuthSessionOut)
def signin(body: SignInRequest):
    client: Client = get_anon_client()
    try:
        result = client.auth.sign_in_with_password(
            {
                "email": str(body.email).strip().lower(),
                "password": body.password,
            }
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=_auth_error_detail(exc) or "Invalid email or password",
        ) from exc

    return _session_response(result.session, result.user)


@router.post("/signout", status_code=status.HTTP_204_NO_CONTENT)
def signout(_user: Annotated[CurrentUser, Depends(get_current_user)]):
    try:
        get_anon_client().auth.sign_out()
    except Exception:
        pass
    return None


@router.get("/me", response_model=UserOut)
def me(user: Annotated[CurrentUser, Depends(get_current_user)]):
    return UserOut(id=str(user.id), email=user.email)

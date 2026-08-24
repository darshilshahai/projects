from __future__ import annotations

from pydantic import BaseModel, EmailStr, Field


class SignUpRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6)


class SignInRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6)


class UserOut(BaseModel):
    id: str
    email: str | None = None


class AuthSessionOut(BaseModel):
    accessToken: str
    refreshToken: str | None = None
    expiresIn: int | None = None
    tokenType: str = "bearer"
    user: UserOut

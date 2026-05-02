from pydantic import EmailStr
from app.schemas.base import AppBaseModel
from app.schemas.user import UserResponse


class LoginRequest(AppBaseModel):
    email: EmailStr
    password: str


class TokenResponse(AppBaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(AppBaseModel):
    refresh_token: str


class LoginResponse(AppBaseModel):
    tokens: TokenResponse
    user: UserResponse
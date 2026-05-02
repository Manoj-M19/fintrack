from pydantic import EmailStr, Field, field_validator
from app.models.user import UserRole
from app.schemas.base import AppBaseModel, TimestampMixin


class UserRegister(AppBaseModel):
    email: EmailStr
    full_name: str = Field(min_length=2, max_length=100)
    password: str = Field(min_length=8, max_length=128)

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit.")
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter.")
        return v


class UserUpdate(AppBaseModel):
    full_name: str | None = Field(default=None, min_length=2, max_length=100)
    password: str | None = Field(default=None, min_length=8, max_length=128)


class UserResponse(TimestampMixin):
    id: int
    email: EmailStr
    full_name: str
    role: UserRole
    is_active: bool


class UserPublic(AppBaseModel):
    id: int
    full_name: str
    email: EmailStr
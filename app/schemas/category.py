from pydantic import Field, field_validator
from app.schemas.base import AppBaseModel, TimestampMixin


class CategoryCreate(AppBaseModel):
    name: str = Field(min_length=1, max_length=100)
    description: str | None = Field(default=None, max_length=255)
    icon: str | None = Field(default=None, max_length=50)
    color: str | None = Field(default=None, max_length=7)

    @field_validator("color")
    @classmethod
    def valid_hex_color(cls, v: str | None) -> str | None:
        if v and not (v.startswith("#") and len(v) in (4, 7)):
            raise ValueError("Color must be a valid hex code e.g. #FF5733")
        return v


class CategoryUpdate(AppBaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    description: str | None = None
    icon: str | None = None
    color: str | None = None


class CategoryResponse(TimestampMixin):
    id: int
    name: str
    description: str | None
    icon: str | None
    color: str | None
    user_id: int | None
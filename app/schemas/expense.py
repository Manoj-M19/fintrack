from datetime import date
from decimal import Decimal
from pydantic import Field, field_validator
from app.models.expense import PaymentMethod
from app.schemas.base import AppBaseModel, TimestampMixin
from app.schemas.category import CategoryResponse


class ExpenseCreate(AppBaseModel):
    amount: Decimal = Field(gt=0, decimal_places=2)
    currency: str = Field(default="INR", min_length=3, max_length=3)
    description: str = Field(min_length=1, max_length=255)
    notes: str | None = Field(default=None, max_length=2000)
    expense_date: date
    payment_method: PaymentMethod = PaymentMethod.CASH
    category_id: int | None = None
    tags: list[str] = Field(default_factory=list)
    receipt_url: str | None = None

    @field_validator("currency")
    @classmethod
    def uppercase_currency(cls, v: str) -> str:
        return v.upper()

    @field_validator("tags")
    @classmethod
    def clean_tags(cls, v: list[str]) -> list[str]:
        return [tag.strip().lower() for tag in v if tag.strip()]


class ExpenseUpdate(AppBaseModel):
    amount: Decimal | None = Field(default=None, gt=0)
    currency: str | None = None
    description: str | None = None
    notes: str | None = None
    expense_date: date | None = None
    payment_method: PaymentMethod | None = None
    category_id: int | None = None
    tags: list[str] | None = None
    receipt_url: str | None = None


class ExpenseFilter(AppBaseModel):
    category_id: int | None = None
    payment_method: PaymentMethod | None = None
    start_date: date | None = None
    end_date: date | None = None
    min_amount: Decimal | None = None
    max_amount: Decimal | None = None
    tag: str | None = None
    search: str | None = None
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)


class ExpenseResponse(TimestampMixin):
    id: int
    amount: Decimal
    currency: str
    description: str
    notes: str | None
    expense_date: date
    payment_method: PaymentMethod
    tags: list[str]
    receipt_url: str | None
    user_id: int
    category_id: int | None
    category: CategoryResponse | None

    @field_validator("tags", mode="before")
    @classmethod
    def parse_tags(cls, v) -> list[str]:
        if isinstance(v, str):
            return [t.strip() for t in v.split(",") if t.strip()]
        return v or []


class ExpenseListResponse(AppBaseModel):
    items: list[ExpenseResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
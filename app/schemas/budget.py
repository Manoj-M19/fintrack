from datetime import date
from decimal import Decimal
from pydantic import Field, model_validator
from app.models.budget import BudgetPeriod
from app.schemas.base import AppBaseModel, TimestampMixin
from app.schemas.category import CategoryResponse


class BudgetCreate(AppBaseModel):
    name: str = Field(min_length=1, max_length=100)
    limit_amount: Decimal = Field(gt=0, decimal_places=2)
    currency: str = Field(default="INR", min_length=3, max_length=3)
    period: BudgetPeriod = BudgetPeriod.MONTHLY
    start_date: date
    end_date: date | None = None
    category_id: int | None = None
    alert_threshold_pct: int = Field(default=80, ge=1, le=100)

    @model_validator(mode="after")
    def validate_dates(self) -> "BudgetCreate":
        if self.period == BudgetPeriod.CUSTOM and self.end_date is None:
            raise ValueError("end_date is required for CUSTOM period budgets.")
        if self.end_date and self.end_date <= self.start_date:
            raise ValueError("end_date must be after start_date.")
        return self


class BudgetUpdate(AppBaseModel):
    name: str | None = None
    limit_amount: Decimal | None = Field(default=None, gt=0)
    alert_threshold_pct: int | None = Field(default=None, ge=1, le=100)
    is_active: bool | None = None
    end_date: date | None = None


class BudgetResponse(TimestampMixin):
    id: int
    name: str
    limit_amount: Decimal
    currency: str
    period: BudgetPeriod
    start_date: date
    end_date: date | None
    is_active: bool
    alert_threshold_pct: int
    alert_sent: bool
    user_id: int
    category_id: int | None
    category: CategoryResponse | None


class BudgetWithUsage(BudgetResponse):
    spent_amount: Decimal
    remaining_amount: Decimal
    usage_percentage: float
    is_over_budget: bool
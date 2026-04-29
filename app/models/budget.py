from datetime import date
from decimal import Decimal
from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Date, ForeignKey, Numeric, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.category import Category
    from app.models.user import User


class BudgetPeriod(str, Enum):
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"
    CUSTOM = "custom"


class Budget(Base):
    """
    Spending limit set by a user for a category over a period.

    Business rules (enforced in BudgetService):
    - A user can only have one active budget per category per period.
    - Alert is triggered by Celery task when spent_amount crosses
      alert_threshold_pct (default 80%) of limit_amount.
    - For CUSTOM period, start_date and end_date are required.
    """

    __tablename__ = "budgets"
    __table_args__ = (
        # Prevent duplicate active budgets for the same user+category+period
        UniqueConstraint(
            "user_id", "category_id", "period", "start_date",
            name="uq_budget_user_category_period_start",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    limit_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="INR", nullable=False)
    period: Mapped[BudgetPeriod] = mapped_column(
        String(20), default=BudgetPeriod.MONTHLY, nullable=False
    )
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Alert config
    alert_threshold_pct: Mapped[int] = mapped_column(
        default=80,
        nullable=False,
        comment="Send alert when (spent / limit) * 100 >= this value",
    )
    alert_sent: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Foreign keys 
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    category_id: Mapped[int | None] = mapped_column(
        ForeignKey("categories.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="NULL = overall budget across all categories",
    )

    #  Relationships 
    user: Mapped["User"] = relationship("User", back_populates="budgets", lazy="noload")
    category: Mapped["Category | None"] = relationship(
        "Category", back_populates="budgets", lazy="noload"
    )

    #  Computed helpers (not persisted) 
    def usage_percentage(self, spent: Decimal) -> float:
        """Return what % of the budget has been spent (0–100+)."""
        if self.limit_amount == 0:
            return 0.0
        return round(float(spent / self.limit_amount * 100), 2)

    def is_over_budget(self, spent: Decimal) -> bool:
        return spent > self.limit_amount

    def should_alert(self, spent: Decimal) -> bool:
        return (
            not self.alert_sent
            and self.usage_percentage(spent) >= self.alert_threshold_pct
        )

    def __repr__(self) -> str:
        return (
            f"<Budget id={self.id} name={self.name!r} "
            f"limit={self.limit_amount} period={self.period} user={self.user_id}>"
        )
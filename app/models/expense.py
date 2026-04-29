from datetime import date
from decimal import Decimal
from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import Date, ForeignKey, Index, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.category import Category
    from app.models.user import User


class PaymentMethod(str, Enum):
    CASH = "cash"
    CREDIT_CARD = "credit_card"
    DEBIT_CARD = "debit_card"
    UPI = "upi"
    NET_BANKING = "net_banking"
    OTHER = "other"


class Expense(Base):
    """
    A single expense entry.

    Amount stored as NUMERIC(12, 2) — avoids floating-point rounding errors.
    currency is a 3-char ISO 4217 code (e.g. "INR", "USD").
    """

    __tablename__ = "expenses"
    __table_args__ = (
        # Common query pattern: fetch all expenses for a user in a date range
        Index("ix_expenses_user_date", "user_id", "expense_date"),
        # Analytics query: group by category for a user
        Index("ix_expenses_user_category", "user_id", "category_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="INR", nullable=False)
    description: Mapped[str] = mapped_column(String(255), nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    expense_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    payment_method: Mapped[PaymentMethod] = mapped_column(
        String(20), default=PaymentMethod.CASH, nullable=False
    )
    tags: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
        comment="Comma-separated tags: 'work,reimbursable,travel'",
    )
    receipt_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)

    #  Foreign keys 
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    category_id: Mapped[int | None] = mapped_column(
        ForeignKey("categories.id", ondelete="SET NULL"), nullable=True, index=True
    )

    #  Relationships
    user: Mapped["User"] = relationship("User", back_populates="expenses", lazy="noload")
    category: Mapped["Category | None"] = relationship(
        "Category", back_populates="expenses", lazy="noload"
    )

    #  Convenience helpers 
    @property
    def tag_list(self) -> list[str]:
        """Return tags as a Python list (empty list if none set)."""
        if not self.tags:
            return []
        return [t.strip() for t in self.tags.split(",") if t.strip()]

    @tag_list.setter
    def tag_list(self, tags: list[str]) -> None:
        self.tags = ",".join(tags) if tags else None

    def __repr__(self) -> str:
        return (
            f"<Expense id={self.id} amount={self.amount} {self.currency} "
            f"date={self.expense_date} user={self.user_id}>"
        )
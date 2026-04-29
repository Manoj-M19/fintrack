from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.budget import Budget
    from app.models.expense import Expense


class Category(Base):
    """
    Expense category (e.g. Food, Transport, Utilities).

    A category is either:
    - system-wide (user_id IS NULL)  — seeded defaults visible to all users
    - user-specific (user_id IS SET) — custom categories created by a user

    Unique constraint prevents a user creating duplicate category names.
    """

    __tablename__ = "categories"
    __table_args__ = (
        UniqueConstraint("name", "user_id", name="uq_category_name_user"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(String(255), nullable=True)
    icon: Mapped[str | None] = mapped_column(String(50), nullable=True)  
    color: Mapped[str | None] = mapped_column(String(7), nullable=True)   

    # NULL = global/system category; set = user-specific category
    user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )

    expenses: Mapped[list["Expense"]] = relationship(
        "Expense", back_populates="category", lazy="noload"
    )
    budgets: Mapped[list["Budget"]] = relationship(
        "Budget", back_populates="category", lazy="noload"
    )

    def __repr__(self) -> str:
        scope = f"user={self.user_id}" if self.user_id else "global"
        return f"<Category id={self.id} name={self.name!r} {scope}>"
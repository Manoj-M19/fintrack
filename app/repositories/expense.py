from datetime import date
from decimal import Decimal

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.models.expense import Expense
from app.repositories.base import BaseRepository


class ExpenseRepository(BaseRepository[Expense]):

    def __init__(self, db: AsyncSession) -> None:
        super().__init__(Expense, db)

    async def get_by_id_and_user(
        self, expense_id: int, user_id: int
    ) -> Expense | None:
        result = await self.db.execute(
            select(Expense)
            .options(joinedload(Expense.category))
            .where(
                Expense.id == expense_id,
                Expense.user_id == user_id,
            )
        )
        return result.scalar_one_or_none()

    async def get_filtered(
        self,
        user_id: int,
        category_id: int | None = None,
        start_date: date | None = None,
        end_date: date | None = None,
        min_amount: Decimal | None = None,
        max_amount: Decimal | None = None,
        search: str | None = None,
        tag: str | None = None,
        skip: int = 0,
        limit: int = 20,
    ) -> tuple[list[Expense], int]:

        filters = [Expense.user_id == user_id]

        if category_id:
            filters.append(Expense.category_id == category_id)
        if start_date:
            filters.append(Expense.expense_date >= start_date)
        if end_date:
            filters.append(Expense.expense_date <= end_date)
        if min_amount:
            filters.append(Expense.amount >= min_amount)
        if max_amount:
            filters.append(Expense.amount <= max_amount)
        if search:
            filters.append(Expense.description.ilike(f"%{search}%"))
        if tag:
            filters.append(Expense.tags.ilike(f"%{tag}%"))

        count_result = await self.db.execute(
            select(func.count()).select_from(Expense).where(and_(*filters))
        )
        total = count_result.scalar_one()

        data_result = await self.db.execute(
            select(Expense)
            .options(joinedload(Expense.category))
            .where(and_(*filters))
            .order_by(Expense.expense_date.desc())
            .offset(skip)
            .limit(limit)
        )
        expenses = list(data_result.scalars().all())

        return expenses, total

    async def get_total_by_category(
        self,
        user_id: int,
        start_date: date,
        end_date: date,
    ) -> list[tuple[int | None, Decimal]]:
        result = await self.db.execute(
            select(Expense.category_id, func.sum(Expense.amount))
            .where(
                Expense.user_id == user_id,
                Expense.expense_date >= start_date,
                Expense.expense_date <= end_date,
            )
            .group_by(Expense.category_id)
            .order_by(func.sum(Expense.amount).desc())
        )
        return list(result.all())

    async def get_monthly_totals(
        self, user_id: int, year: int
    ) -> list[tuple[int, Decimal]]:
        result = await self.db.execute(
            select(
                func.extract("month", Expense.expense_date).label("month"),
                func.sum(Expense.amount).label("total"),
            )
            .where(
                Expense.user_id == user_id,
                func.extract("year", Expense.expense_date) == year,
            )
            .group_by("month")
            .order_by("month")
        )
        return list(result.all())
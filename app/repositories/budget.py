from datetime import date

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.models.budget import Budget
from app.repositories.base import BaseRepository


class BudgetRepository(BaseRepository[Budget]):

    def __init__(self, db: AsyncSession) -> None:
        super().__init__(Budget, db)

    async def get_by_id_and_user(
        self, budget_id: int, user_id: int
    ) -> Budget | None:
        result = await self.db.execute(
            select(Budget)
            .options(joinedload(Budget.category))
            .where(
                Budget.id == budget_id,
                Budget.user_id == user_id,
            )
        )
        return result.scalar_one_or_none()

    async def get_active_by_user(self, user_id: int) -> list[Budget]:
        result = await self.db.execute(
            select(Budget)
            .options(joinedload(Budget.category))
            .where(
                Budget.user_id == user_id,
                Budget.is_active == True,
            )
            .order_by(Budget.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_active_for_category(
        self,
        user_id: int,
        category_id: int,
        reference_date: date,
    ) -> Budget | None:
        result = await self.db.execute(
            select(Budget).where(
                and_(
                    Budget.user_id == user_id,
                    Budget.category_id == category_id,
                    Budget.is_active == True,
                    Budget.start_date <= reference_date,
                )
            )
        )
        return result.scalar_one_or_none()

    async def get_budgets_needing_alert(self) -> list[Budget]:
        result = await self.db.execute(
            select(Budget).where(
                Budget.is_active == True,
                Budget.alert_sent == False,
            )
        )
        return list(result.scalars().all())
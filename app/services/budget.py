import math

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.budget import Budget
from app.repositories.budget import BudgetRepository
from app.repositories.expense import ExpenseRepository
from app.schemas.budget import (
    BudgetCreate,
    BudgetResponse,
    BudgetUpdate,
    BudgetWithUsage,
)


class BudgetService:

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.repo = BudgetRepository(db)
        self.expense_repo = ExpenseRepository(db)

    async def create(self, user_id: int, data: BudgetCreate) -> BudgetResponse:
        budget = Budget(
            user_id=user_id,
            name=data.name,
            limit_amount=data.limit_amount,
            currency=data.currency,
            period=data.period,
            start_date=data.start_date,
            end_date=data.end_date,
            category_id=data.category_id,
            alert_threshold_pct=data.alert_threshold_pct,
        )
        budget = await self.repo.create(budget)
        return BudgetResponse.model_validate(budget)

    async def list(self, user_id: int) -> list[BudgetWithUsage]:
        budgets = await self.repo.get_active_by_user(user_id)
        result = []
        for budget in budgets:
            spent = await self._get_spent(budget)
            remaining = budget.limit_amount - spent
            result.append(
                BudgetWithUsage(
                    **BudgetResponse.model_validate(budget).model_dump(),
                    spent_amount=spent,
                    remaining_amount=remaining,
                    usage_percentage=budget.usage_percentage(spent),
                    is_over_budget=budget.is_over_budget(spent),
                )
            )
        return result

    async def get_by_id(self, user_id: int, budget_id: int) -> BudgetWithUsage:
        budget = await self.repo.get_by_id_and_user(budget_id, user_id)
        if not budget:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Budget not found.",
            )
        spent = await self._get_spent(budget)
        remaining = budget.limit_amount - spent
        return BudgetWithUsage(
            **BudgetResponse.model_validate(budget).model_dump(),
            spent_amount=spent,
            remaining_amount=remaining,
            usage_percentage=budget.usage_percentage(spent),
            is_over_budget=budget.is_over_budget(spent),
        )

    async def update(
        self, user_id: int, budget_id: int, data: BudgetUpdate
    ) -> BudgetResponse:
        budget = await self.repo.get_by_id_and_user(budget_id, user_id)
        if not budget:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Budget not found.",
            )
        update_data = data.model_dump(exclude_none=True)
        budget = await self.repo.update(budget, update_data)
        return BudgetResponse.model_validate(budget)

    async def delete(self, user_id: int, budget_id: int) -> None:
        budget = await self.repo.get_by_id_and_user(budget_id, user_id)
        if not budget:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Budget not found.",
            )
        await self.repo.delete(budget)

    async def _get_spent(self, budget: Budget):
        """Calculate total spent for a budget's category and date range."""
        from decimal import Decimal
        totals = await self.expense_repo.get_total_by_category(
            user_id=budget.user_id,
            start_date=budget.start_date,
            end_date=budget.end_date or budget.start_date,
        )
        if budget.category_id is None:
            # Overall budget — sum all categories
            return sum((t[1] for t in totals), Decimal("0"))
        for category_id, total in totals:
            if category_id == budget.category_id:
                return total
        return Decimal("0")
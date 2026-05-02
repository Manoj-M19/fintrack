import math
from datetime import date
from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.expense import Expense
from app.repositories.expense import ExpenseRepository
from app.schemas.expense import (
    ExpenseCreate,
    ExpenseFilter,
    ExpenseListResponse,
    ExpenseResponse,
    ExpenseUpdate,
)


class ExpenseService:

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.repo = ExpenseRepository(db)

    async def create(self, user_id: int, data: ExpenseCreate) -> ExpenseResponse:
        expense = Expense(
            user_id=user_id,
            amount=data.amount,
            currency=data.currency,
            description=data.description,
            notes=data.notes,
            expense_date=data.expense_date,
            payment_method=data.payment_method,
            category_id=data.category_id,
            receipt_url=data.receipt_url,
            tags=",".join(data.tags) if data.tags else None,
        )
        expense = await self.repo.create(expense)
        return ExpenseResponse.model_validate(expense)

    async def get_by_id(self, user_id: int, expense_id: int) -> ExpenseResponse:
        expense = await self.repo.get_by_id_and_user(expense_id, user_id)
        if not expense:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Expense not found.",
            )
        return ExpenseResponse.model_validate(expense)

    async def list(
        self, user_id: int, filters: ExpenseFilter
    ) -> ExpenseListResponse:
        skip = (filters.page - 1) * filters.page_size
        expenses, total = await self.repo.get_filtered(
            user_id=user_id,
            category_id=filters.category_id,
            start_date=filters.start_date,
            end_date=filters.end_date,
            min_amount=filters.min_amount,
            max_amount=filters.max_amount,
            search=filters.search,
            tag=filters.tag,
            skip=skip,
            limit=filters.page_size,
        )
        return ExpenseListResponse(
            items=[ExpenseResponse.model_validate(e) for e in expenses],
            total=total,
            page=filters.page,
            page_size=filters.page_size,
            total_pages=math.ceil(total / filters.page_size) if total else 0,
        )

    async def update(
        self, user_id: int, expense_id: int, data: ExpenseUpdate
    ) -> ExpenseResponse:
        expense = await self.repo.get_by_id_and_user(expense_id, user_id)
        if not expense:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Expense not found.",
            )

        update_data = data.model_dump(exclude_none=True)

        # Convert tags list to comma-separated string for DB
        if "tags" in update_data:
            update_data["tags"] = ",".join(update_data["tags"])

        expense = await self.repo.update(expense, update_data)
        return ExpenseResponse.model_validate(expense)

    async def delete(self, user_id: int, expense_id: int) -> None:
        expense = await self.repo.get_by_id_and_user(expense_id, user_id)
        if not expense:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Expense not found.",
            )
        await self.repo.delete(expense)
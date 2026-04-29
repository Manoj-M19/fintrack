from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import CurrentUserID
from app.schemas.expense import (
    ExpenseCreate,
    ExpenseFilter,
    ExpenseListResponse,
    ExpenseResponse,
    ExpenseUpdate,
)
from app.services.expense import ExpenseService

router = APIRouter()


@router.post("", response_model=ExpenseResponse, status_code=201)
async def create_expense(
    data: ExpenseCreate,
    user_id: CurrentUserID,
    db: AsyncSession = Depends(get_db),
):
    return await ExpenseService(db).create(user_id, data)


@router.get("", response_model=ExpenseListResponse)
async def list_expenses(
    user_id: CurrentUserID,
    db: AsyncSession = Depends(get_db),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    search: str | None = Query(default=None),
    category_id: int | None = Query(default=None),
    tag: str | None = Query(default=None),
):
    filters = ExpenseFilter(
        page=page,
        page_size=page_size,
        search=search,
        category_id=category_id,
        tag=tag,
    )
    return await ExpenseService(db).list(user_id, filters)


@router.get("/{expense_id}", response_model=ExpenseResponse)
async def get_expense(
    expense_id: int,
    user_id: CurrentUserID,
    db: AsyncSession = Depends(get_db),
):
    return await ExpenseService(db).get_by_id(user_id, expense_id)


@router.put("/{expense_id}", response_model=ExpenseResponse)
async def update_expense(
    expense_id: int,
    data: ExpenseUpdate,
    user_id: CurrentUserID,
    db: AsyncSession = Depends(get_db),
):
    return await ExpenseService(db).update(user_id, expense_id, data)


@router.delete("/{expense_id}", status_code=204)
async def delete_expense(
    expense_id: int,
    user_id: CurrentUserID,
    db: AsyncSession = Depends(get_db),
):
    await ExpenseService(db).delete(user_id, expense_id)
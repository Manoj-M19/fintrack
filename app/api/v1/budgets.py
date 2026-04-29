from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import CurrentUserID
from app.schemas.budget import (
    BudgetCreate,
    BudgetResponse,
    BudgetUpdate,
    BudgetWithUsage,
)
from app.services.budget import BudgetService

router = APIRouter()


@router.post("", response_model=BudgetResponse, status_code=201)
async def create_budget(
    data: BudgetCreate,
    user_id: CurrentUserID,
    db: AsyncSession = Depends(get_db),
):
    return await BudgetService(db).create(user_id, data)


@router.get("", response_model=list[BudgetWithUsage])
async def list_budgets(
    user_id: CurrentUserID,
    db: AsyncSession = Depends(get_db),
):
    return await BudgetService(db).list(user_id)


@router.get("/{budget_id}", response_model=BudgetWithUsage)
async def get_budget(
    budget_id: int,
    user_id: CurrentUserID,
    db: AsyncSession = Depends(get_db),
):
    return await BudgetService(db).get_by_id(user_id, budget_id)


@router.put("/{budget_id}", response_model=BudgetResponse)
async def update_budget(
    budget_id: int,
    data: BudgetUpdate,
    user_id: CurrentUserID,
    db: AsyncSession = Depends(get_db),
):
    return await BudgetService(db).update(user_id, budget_id, data)


@router.delete("/{budget_id}", status_code=204)
async def delete_budget(
    budget_id: int,
    user_id: CurrentUserID,
    db: AsyncSession = Depends(get_db),
):
    await BudgetService(db).delete(user_id, budget_id)
from fastapi import APIRouter
from app.api.v1 import auth, expenses, budgets, reports

api_router = APIRouter()

api_router.include_router(auth.router,     prefix="/auth",     tags=["Auth"])
api_router.include_router(expenses.router, prefix="/expenses", tags=["Expenses"])
api_router.include_router(budgets.router,  prefix="/budgets",  tags=["Budgets"])
api_router.include_router(reports.router,  prefix="/reports",  tags=["Reports"])
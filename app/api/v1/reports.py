from datetime import date

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
import io

from app.core.database import get_db
from app.core.dependencies import CurrentUserID
from app.services.report import CategoryReport, MonthlySummary, ReportService

router = APIRouter()


@router.get("/monthly", response_model=MonthlySummary)
async def monthly_summary(
    user_id: CurrentUserID,
    db: AsyncSession = Depends(get_db),
    year: int = Query(default=2024, ge=2000, le=2100),
):
    return await ReportService(db).monthly_summary(user_id, year)


@router.get("/by-category", response_model=CategoryReport)
async def category_breakdown(
    user_id: CurrentUserID,
    db: AsyncSession = Depends(get_db),
    start_date: date = Query(...),
    end_date: date = Query(...),
):
    return await ReportService(db).category_breakdown(user_id, start_date, end_date)


@router.get("/export/csv")
async def export_csv(
    user_id: CurrentUserID,
    db: AsyncSession = Depends(get_db),
    start_date: date = Query(...),
    end_date: date = Query(...),
):
    csv_data = await ReportService(db).export_csv(user_id, start_date, end_date)
    return StreamingResponse(
        io.StringIO(csv_data),
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=expenses_{start_date}_{end_date}.csv"
        },
    )
import csv
import io
from datetime import date
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.category import CategoryRepository
from app.repositories.expense import ExpenseRepository
from app.schemas.base import AppBaseModel


class CategoryBreakdown(AppBaseModel):
    category_id: int | None
    category_name: str
    total_amount: Decimal
    percentage: float
    expense_count: int


class MonthlyTotal(AppBaseModel):
    month: int
    month_name: str
    total_amount: Decimal


class MonthlySummary(AppBaseModel):
    year: int
    totals: list[MonthlyTotal]
    grand_total: Decimal
    highest_month: str
    lowest_month: str


class CategoryReport(AppBaseModel):
    start_date: date
    end_date: date
    grand_total: Decimal
    breakdown: list[CategoryBreakdown]


MONTH_NAMES = [
    "", "January", "February", "March", "April",
    "May", "June", "July", "August", "September",
    "October", "November", "December",
]


class ReportService:

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.expense_repo = ExpenseRepository(db)
        self.category_repo = CategoryRepository(db)

    async def monthly_summary(
        self, user_id: int, year: int
    ) -> MonthlySummary:
        rows = await self.expense_repo.get_monthly_totals(user_id, year)

        totals = []
        for month_num, total in rows:
            month_int = int(month_num)
            totals.append(
                MonthlyTotal(
                    month=month_int,
                    month_name=MONTH_NAMES[month_int],
                    total_amount=total,
                )
            )

        grand_total = sum((t.total_amount for t in totals), Decimal("0"))
        highest = max(totals, key=lambda t: t.total_amount) if totals else None
        lowest = min(totals, key=lambda t: t.total_amount) if totals else None

        return MonthlySummary(
            year=year,
            totals=totals,
            grand_total=grand_total,
            highest_month=highest.month_name if highest else "N/A",
            lowest_month=lowest.month_name if lowest else "N/A",
        )

    async def category_breakdown(
        self,
        user_id: int,
        start_date: date,
        end_date: date,
    ) -> CategoryReport:
        rows = await self.expense_repo.get_total_by_category(
            user_id, start_date, end_date
        )
        categories = await self.category_repo.get_visible_to_user(user_id)
        category_map = {c.id: c.name for c in categories}

        grand_total = sum((r[1] for r in rows), Decimal("0"))

        breakdown = []
        for category_id, total in rows:
            name = category_map.get(category_id, "Uncategorized") if category_id else "Uncategorized"
            percentage = round(float(total / grand_total * 100), 2) if grand_total else 0.0
            breakdown.append(
                CategoryBreakdown(
                    category_id=category_id,
                    category_name=name,
                    total_amount=total,
                    percentage=percentage,
                    expense_count=0,  # can be extended later
                )
            )

        return CategoryReport(
            start_date=start_date,
            end_date=end_date,
            grand_total=grand_total,
            breakdown=breakdown,
        )

    async def export_csv(
        self,
        user_id: int,
        start_date: date,
        end_date: date,
    ) -> str:
        """Returns expenses as a CSV string for download."""
        expenses, _ = await self.expense_repo.get_filtered(
            user_id=user_id,
            start_date=start_date,
            end_date=end_date,
            skip=0,
            limit=10000,
        )

        output = io.StringIO()
        writer = csv.writer(output)

        # Header row
        writer.writerow([
            "ID", "Date", "Description", "Amount",
            "Currency", "Category", "Payment Method", "Tags", "Notes",
        ])

        for e in expenses:
            writer.writerow([
                e.id,
                e.expense_date,
                e.description,
                e.amount,
                e.currency,
                e.category.name if e.category else "",
                e.payment_method,
                e.tags or "",
                e.notes or "",
            ])

        return output.getvalue()
import asyncio
from decimal import Decimal

from app.workers.celery_app import celery_app


@celery_app.task(name="tasks.send_budget_alert_email", bind=True, max_retries=3)
def send_budget_alert_email(
    self, user_id: int, budget_id: int, usage_pct: float
) -> dict:
    """
    Triggered when a user's spending crosses the alert threshold.
    In production replace print() with real SMTP / SendGrid call.
    """
    try:
        print(
            f"[ALERT] User {user_id} — Budget {budget_id} "
            f"is at {usage_pct:.1f}% usage!"
        )
        # TODO: replace with actual email sending
        # send_email(to=user_email, subject="Budget Alert", body=...)
        return {"status": "sent", "user_id": user_id, "budget_id": budget_id}
    except Exception as exc:
        raise self.retry(exc=exc, countdown=60)


@celery_app.task(name="tasks.check_all_budgets", bind=True)
def check_all_budgets(self) -> dict:
    """
    Periodic task — runs every hour via Celery Beat.
    Checks all active budgets and sends alerts where needed.
    """
    asyncio.run(_check_budgets_async())
    return {"status": "done"}


async def _check_budgets_async() -> None:
    from app.core.database import AsyncSessionLocal
    from app.repositories.budget import BudgetRepository
    from app.repositories.expense import ExpenseRepository

    async with AsyncSessionLocal() as db:
        budget_repo = BudgetRepository(db)
        expense_repo = ExpenseRepository(db)

        budgets = await budget_repo.get_budgets_needing_alert()

        for budget in budgets:
            totals = await expense_repo.get_total_by_category(
                user_id=budget.user_id,
                start_date=budget.start_date,
                end_date=budget.end_date or budget.start_date,
            )
            spent = Decimal("0")
            for cat_id, total in totals:
                if budget.category_id is None or cat_id == budget.category_id:
                    spent += total

            if budget.should_alert(spent):
                usage_pct = budget.usage_percentage(spent)
                send_budget_alert_email.delay(
                    budget.user_id, budget.id, usage_pct
                )
                # Mark alert as sent
                budget.alert_sent = True
                await db.commit()
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.category import Category
from app.repositories.base import BaseRepository


class CategoryRepository(BaseRepository[Category]):

    def __init__(self, db: AsyncSession) -> None:
        super().__init__(Category, db)

    async def get_visible_to_user(self, user_id: int) -> list[Category]:
        result = await self.db.execute(
            select(Category)
            .where(
                or_(
                    Category.user_id == None,
                    Category.user_id == user_id,
                )
            )
            .order_by(Category.name)
        )
        return list(result.scalars().all())

    async def get_by_name_and_user(
        self, name: str, user_id: int
    ) -> Category | None:
        result = await self.db.execute(
            select(Category).where(
                Category.name == name,
                Category.user_id == user_id,
            )
        )
        return result.scalar_one_or_none()
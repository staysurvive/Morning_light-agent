from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.base_repository import BaseRepository
from src.modules.provider.model import ModelProvider


class ProviderRepository(BaseRepository[ModelProvider]):
    SEARCH_FIELDS = ["name", "type", "endpoint"]

    def __init__(self, db: AsyncSession):
        super().__init__(ModelProvider, db)

    async def get_by_name(self, name: str) -> ModelProvider | None:
        return await self.db.scalar(select(ModelProvider).where(ModelProvider.name == name))

    async def search_page(
        self,
        offset: int,
        limit: int,
        keyword: str | None,
    ) -> tuple[list[ModelProvider], int]:
        return await self.get_page(offset, limit, keyword, self.SEARCH_FIELDS)

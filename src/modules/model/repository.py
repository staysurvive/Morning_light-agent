from sqlalchemy import func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.base_repository import BaseRepository
from src.modules.model.model import LLMModel


class ModelRepository(BaseRepository[LLMModel]):
    def __init__(self, db: AsyncSession):
        super().__init__(LLMModel, db)

    async def get_by_provider_model_id(self, provider_id: int, model_id: str) -> LLMModel | None:
        return await self.db.scalar(
            select(LLMModel).where(
                LLMModel.provider_id == provider_id,
                LLMModel.model_id == model_id,
            )
        )

    async def clear_default(self, exclude_id: int | None = None) -> None:
        stmt = update(LLMModel).where(LLMModel.is_default.is_(True))
        if exclude_id is not None:
            stmt = stmt.where(LLMModel.id != exclude_id)
        await self.db.execute(stmt.values(is_default=False))

    async def search_page(
        self,
        offset: int,
        limit: int,
        keyword: str | None,
        provider_id: int | None,
    ) -> tuple[list[LLMModel], int]:
        stmt = select(LLMModel)
        if provider_id is not None:
            stmt = stmt.where(LLMModel.provider_id == provider_id)
        if keyword:
            pattern = f"%{keyword}%"
            stmt = stmt.where(or_(LLMModel.name.like(pattern), LLMModel.model_id.like(pattern)))
        total = await self.db.scalar(select(func.count()).select_from(stmt.subquery()))
        result = await self.db.execute(stmt.order_by(LLMModel.id.desc()).offset(offset).limit(limit))
        return list(result.scalars().all()), int(total or 0)

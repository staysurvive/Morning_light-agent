import re

from sqlalchemy import func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.base_repository import BaseRepository
from src.modules.prompt.model import Prompt, PromptVersion


class PromptRepository(BaseRepository[Prompt]):
    def __init__(self, db: AsyncSession):
        super().__init__(Prompt, db)

    async def get_by_name(self, name: str) -> Prompt | None:
        return await self.db.scalar(select(Prompt).where(Prompt.name == name))

    async def search_page(self, offset: int, limit: int, keyword: str | None) -> tuple[list[Prompt], int]:
        stmt = select(Prompt)
        if keyword:
            pattern = f"%{keyword}%"
            stmt = stmt.where(or_(Prompt.name.like(pattern), Prompt.description.like(pattern), Prompt.category.like(pattern)))
        total = await self.db.scalar(select(func.count()).select_from(stmt.subquery()))
        result = await self.db.execute(stmt.order_by(Prompt.id.desc()).offset(offset).limit(limit))
        return list(result.scalars().all()), int(total or 0)


class PromptVersionRepository(BaseRepository[PromptVersion]):
    def __init__(self, db: AsyncSession):
        super().__init__(PromptVersion, db)

    async def list_for_prompt(self, prompt_id: int) -> list[PromptVersion]:
        result = await self.db.execute(
            select(PromptVersion)
            .where(PromptVersion.prompt_id == prompt_id)
            .order_by(PromptVersion.id.desc())
        )
        return list(result.scalars().all())

    async def get_by_version(self, prompt_id: int, version: str) -> PromptVersion | None:
        return await self.db.scalar(
            select(PromptVersion).where(
                PromptVersion.prompt_id == prompt_id,
                PromptVersion.version == version,
            )
        )

    async def clear_current(self, prompt_id: int) -> None:
        await self.db.execute(
            update(PromptVersion)
            .where(PromptVersion.prompt_id == prompt_id, PromptVersion.is_current.is_(True))
            .values(is_current=False)
        )

    async def next_version(self, prompt_id: int) -> str:
        versions = await self.list_for_prompt(prompt_id)
        if not versions:
            return "v1.0"
        numbers = []
        for item in versions:
            match = re.fullmatch(r"v(\d+)\.(\d+)", item.version)
            if match:
                numbers.append((int(match.group(1)), int(match.group(2))))
        if not numbers:
            return f"v1.{len(versions)}"
        major, minor = max(numbers)
        return f"v{major}.{minor + 1}"

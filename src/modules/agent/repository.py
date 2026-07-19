import re

from sqlalchemy import func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.base_repository import BaseRepository
from src.modules.agent.model import Agent, AgentVersion


class AgentRepository(BaseRepository[Agent]):
    def __init__(self, db: AsyncSession):
        super().__init__(Agent, db)

    async def get_by_name(self, name: str) -> Agent | None:
        return await self.db.scalar(select(Agent).where(Agent.name == name))

    async def search_page(self, offset: int, limit: int, keyword: str | None) -> tuple[list[Agent], int]:
        stmt = select(Agent)
        if keyword:
            pattern = f"%{keyword}%"
            stmt = stmt.where(or_(Agent.name.like(pattern), Agent.description.like(pattern)))
        total = await self.db.scalar(select(func.count()).select_from(stmt.subquery()))
        result = await self.db.execute(stmt.order_by(Agent.id.desc()).offset(offset).limit(limit))
        return list(result.scalars().all()), int(total or 0)


class AgentVersionRepository(BaseRepository[AgentVersion]):
    def __init__(self, db: AsyncSession):
        super().__init__(AgentVersion, db)

    async def list_for_agent(self, agent_id: int) -> list[AgentVersion]:
        result = await self.db.execute(
            select(AgentVersion)
            .where(AgentVersion.agent_id == agent_id)
            .order_by(AgentVersion.id.desc())
        )
        return list(result.scalars().all())

    async def get_by_version(self, agent_id: int, version: str) -> AgentVersion | None:
        return await self.db.scalar(
            select(AgentVersion).where(
                AgentVersion.agent_id == agent_id,
                AgentVersion.version == version,
            )
        )

    async def clear_current(self, agent_id: int) -> None:
        await self.db.execute(
            update(AgentVersion)
            .where(AgentVersion.agent_id == agent_id, AgentVersion.is_current.is_(True))
            .values(is_current=False)
        )

    async def next_version(self, agent_id: int) -> str:
        versions = await self.list_for_agent(agent_id)
        if not versions:
            return "v1.0"
        parsed = []
        for item in versions:
            match = re.fullmatch(r"v(\d+)\.(\d+)", item.version)
            if match:
                parsed.append((int(match.group(1)), int(match.group(2))))
        if not parsed:
            return f"v1.{len(versions)}"
        major, minor = max(parsed)
        return f"v{major}.{minor + 1}"

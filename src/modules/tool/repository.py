from datetime import datetime, timedelta

from sqlalchemy import case, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.base_repository import BaseRepository
from src.modules.tool.model import Tool, ToolExecution


class ToolRepository(BaseRepository[Tool]):
    def __init__(self, db: AsyncSession):
        super().__init__(Tool, db)

    async def get_by_name(self, name: str) -> Tool | None:
        return await self.db.scalar(select(Tool).where(Tool.name == name))

    async def search_page(self, offset: int, limit: int, keyword: str | None) -> tuple[list[Tool], int]:
        stmt = select(Tool)
        if keyword:
            pattern = f"%{keyword}%"
            stmt = stmt.where(or_(Tool.name.like(pattern), Tool.description.like(pattern)))
        total = await self.db.scalar(select(func.count()).select_from(stmt.subquery()))
        result = await self.db.execute(stmt.order_by(Tool.id.desc()).offset(offset).limit(limit))
        items = list(result.scalars().all())
        for item in items:
            await self.refresh_metrics(item)
        return items, int(total or 0)

    async def refresh_metrics(self, tool: Tool) -> Tool:
        since = datetime.now() - timedelta(days=7)
        row = (await self.db.execute(
            select(
                func.count(ToolExecution.id),
                func.coalesce(func.sum(case((ToolExecution.success.is_(True), 1), else_=0)), 0),
                func.coalesce(func.avg(ToolExecution.latency_ms), 0),
            ).where(ToolExecution.tool_id == tool.id, ToolExecution.executed_at >= since)
        )).one()
        count, success_count, avg_latency = int(row[0]), int(row[1]), float(row[2])
        tool.call_count_7d = count
        tool.success_rate = (success_count / count * 100) if count else 0
        tool.avg_latency = avg_latency
        await self.db.flush()
        return tool


class ToolExecutionRepository(BaseRepository[ToolExecution]):
    def __init__(self, db: AsyncSession):
        super().__init__(ToolExecution, db)

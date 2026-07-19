from datetime import datetime, timedelta

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.base_repository import BaseRepository
from src.modules.agent.model import Agent
from src.modules.conversation.model import Conversation, ConversationAnnotation, ConversationTurn, TraceStep


class ConversationRepository(BaseRepository[Conversation]):
    def __init__(self, db: AsyncSession):
        super().__init__(Conversation, db)

    async def search_page(
        self,
        offset: int,
        limit: int,
        keyword: str | None,
        agent_id: int | None,
        user_id: int | None,
        status: str | None,
        start_at: datetime | None,
        end_at: datetime | None,
    ) -> tuple[list[Conversation], int]:
        stmt = select(Conversation)
        if keyword:
            pattern = f"%{keyword}%"
            stmt = stmt.where(or_(
                Conversation.agent_name_snapshot.like(pattern),
                Conversation.user_name_snapshot.like(pattern),
            ))
        if agent_id is not None:
            stmt = stmt.where(Conversation.agent_id == agent_id)
        if user_id is not None:
            stmt = stmt.where(Conversation.user_id == user_id)
        if status:
            stmt = stmt.where(Conversation.status == status)
        if start_at:
            stmt = stmt.where(Conversation.started_at >= start_at)
        if end_at:
            stmt = stmt.where(Conversation.started_at < end_at)
        total = await self.db.scalar(select(func.count()).select_from(stmt.subquery()))
        result = await self.db.execute(stmt.order_by(Conversation.started_at.desc()).offset(offset).limit(limit))
        return list(result.scalars().all()), int(total or 0)

    async def list_between(
        self,
        start_at: datetime,
        end_at: datetime,
        agent_id: int | None = None,
        model_id: int | None = None,
    ) -> list[Conversation]:
        stmt = select(Conversation).where(
            Conversation.started_at >= start_at,
            Conversation.started_at < end_at,
        )
        if agent_id is not None:
            stmt = stmt.where(Conversation.agent_id == agent_id)
        if model_id is not None:
            stmt = stmt.where(Conversation.model_id == model_id)
        result = await self.db.execute(stmt.order_by(Conversation.started_at))
        return list(result.scalars().all())

    async def refresh_agent_metrics(self, agent_id: int | None) -> None:
        if agent_id is None:
            return
        agent = await self.db.get(Agent, agent_id)
        if not agent:
            return
        since = datetime.now() - timedelta(days=7)
        result = (await self.db.execute(select(
            func.count(Conversation.id),
            func.coalesce(func.sum((Conversation.status == "completed")), 0),
        ).where(Conversation.agent_id == agent_id, Conversation.started_at >= since))).one()
        count = int(result[0])
        success = int(result[1])
        agent.call_count_7d = count
        agent.success_rate = success / count * 100 if count else 0
        await self.db.flush()


class TurnRepository(BaseRepository[ConversationTurn]):
    def __init__(self, db: AsyncSession):
        super().__init__(ConversationTurn, db)

    async def list_for_conversation(self, conversation_id: int) -> list[ConversationTurn]:
        result = await self.db.execute(select(ConversationTurn).where(
            ConversationTurn.conversation_id == conversation_id
        ).order_by(ConversationTurn.timestamp, ConversationTurn.id))
        return list(result.scalars().all())

    async def get_for_conversation(self, conversation_id: int, turn_id: int) -> ConversationTurn | None:
        return await self.db.scalar(select(ConversationTurn).where(
            ConversationTurn.id == turn_id,
            ConversationTurn.conversation_id == conversation_id,
        ))


class TraceRepository(BaseRepository[TraceStep]):
    def __init__(self, db: AsyncSession):
        super().__init__(TraceStep, db)

    async def list_for_turn(self, turn_id: int) -> list[TraceStep]:
        result = await self.db.execute(select(TraceStep).where(
            TraceStep.turn_id == turn_id
        ).order_by(TraceStep.start_time, TraceStep.id))
        return list(result.scalars().all())


class AnnotationRepository(BaseRepository[ConversationAnnotation]):
    def __init__(self, db: AsyncSession):
        super().__init__(ConversationAnnotation, db)

    async def get_for_conversation(self, conversation_id: int) -> ConversationAnnotation | None:
        return await self.db.scalar(select(ConversationAnnotation).where(
            ConversationAnnotation.conversation_id == conversation_id
        ))

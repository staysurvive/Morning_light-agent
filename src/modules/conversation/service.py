from datetime import datetime
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from src.core.exceptions import BizException
from src.modules.agent.repository import AgentRepository
from src.modules.conversation.model import Conversation, ConversationAnnotation, ConversationTurn, TraceStep
from src.modules.conversation.repository import AnnotationRepository, ConversationRepository, TraceRepository, TurnRepository
from src.modules.conversation.schema import AnnotationUpsert, ConversationCreate, ConversationUpdate, TraceCreate, TurnCreate
from src.modules.user.model import User


class ConversationService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = ConversationRepository(db)
        self.turn_repo = TurnRepository(db)
        self.trace_repo = TraceRepository(db)
        self.annotation_repo = AnnotationRepository(db)
        self.agent_repo = AgentRepository(db)

    async def create_conversation(self, data: ConversationCreate, current_user: User) -> Conversation:
        agent = await self.agent_repo.get_by_id(data.agent_id)
        if not agent:
            raise BizException(code=400, message="Agent 不存在")
        user = current_user
        if data.user_id is not None:
            user = await self.db.get(User, data.user_id)
            if not user:
                raise BizException(code=400, message="用户不存在")
        conversation = Conversation(
            agent_id=agent.id,
            user_id=user.id,
            model_id=agent.model_id,
            agent_name_snapshot=agent.name,
            user_name_snapshot=user.username,
            model_name_snapshot=agent.model_name,
            status="active",
            tags=list(dict.fromkeys(tag.strip() for tag in data.tags if tag.strip())),
            started_at=data.started_at or datetime.now(),
        )
        conversation = await self.repo.create(conversation)
        await self.repo.refresh_agent_metrics(agent.id)
        return conversation

    async def get_conversation(self, conversation_id: int) -> Conversation:
        conversation = await self.repo.get_by_id(conversation_id)
        if not conversation:
            raise BizException(code=404, message="会话不存在")
        return conversation

    async def search_page(self, *args):
        return await self.repo.search_page(*args)

    async def update_conversation(self, conversation_id: int, data: ConversationUpdate) -> Conversation:
        conversation = await self.get_conversation(conversation_id)
        values = data.model_dump(exclude_unset=True)
        if data.status is not None:
            conversation.status = data.status
            if data.status != "active" and "ended_at" not in values:
                conversation.ended_at = datetime.now()
        if data.cost is not None:
            conversation.cost = Decimal(str(data.cost))
        if data.duration is not None:
            conversation.duration = data.duration
        if data.tags is not None:
            conversation.tags = list(dict.fromkeys(tag.strip() for tag in data.tags if tag.strip()))
        if "error_message" in values:
            conversation.error_message = data.error_message.strip() if data.error_message else None
        if "ended_at" in values:
            conversation.ended_at = data.ended_at
        conversation = await self.repo.update(conversation)
        await self.repo.refresh_agent_metrics(conversation.agent_id)
        return conversation

    async def delete_conversation(self, conversation_id: int) -> None:
        conversation = await self.get_conversation(conversation_id)
        agent_id = conversation.agent_id
        await self.repo.delete(conversation)
        await self.repo.refresh_agent_metrics(agent_id)

    async def add_turn(self, conversation_id: int, data: TurnCreate) -> ConversationTurn:
        conversation = await self.get_conversation(conversation_id)
        if conversation.status != "active":
            raise BizException(code=400, message="只能向进行中的会话添加轮次")
        turn = await self.turn_repo.create(ConversationTurn(
            conversation_id=conversation_id,
            role=data.role,
            content=data.content,
            timestamp=data.timestamp or datetime.now(),
            token_count=data.token_count,
            tool_calls=data.tool_calls,
        ))
        if data.role == "user":
            conversation.turn_count += 1
            conversation.input_tokens += data.token_count
        elif data.role == "assistant":
            conversation.output_tokens += data.token_count
        await self.repo.update(conversation)
        return turn

    async def list_turns(self, conversation_id: int) -> list[ConversationTurn]:
        await self.get_conversation(conversation_id)
        return await self.turn_repo.list_for_conversation(conversation_id)

    async def add_trace(self, turn_id: int, data: TraceCreate) -> TraceStep:
        turn = await self.turn_repo.get_by_id(turn_id)
        if not turn:
            raise BizException(code=404, message="会话轮次不存在")
        duration = data.duration
        if duration is None:
            duration = max(0, round((data.end_time - data.start_time).total_seconds() * 1000))
        return await self.trace_repo.create(TraceStep(
            turn_id=turn_id,
            type=data.type,
            name=data.name.strip(),
            input_data=data.input,
            output_data=data.output,
            start_time=data.start_time,
            end_time=data.end_time,
            duration=duration,
            status=data.status,
            prompt_tokens=data.prompt_tokens,
            completion_tokens=data.completion_tokens,
            total_tokens=data.prompt_tokens + data.completion_tokens,
            metadata_json=data.metadata,
        ))

    async def list_trace(self, turn_id: int) -> list[TraceStep]:
        if not await self.turn_repo.get_by_id(turn_id):
            raise BizException(code=404, message="会话轮次不存在")
        return await self.trace_repo.list_for_turn(turn_id)

    def serialize_trace(self, item: TraceStep) -> dict:
        return {
            "id": item.id, "turn_id": item.turn_id, "type": item.type, "name": item.name,
            "input": item.input_data, "output": item.output_data,
            "start_time": item.start_time, "end_time": item.end_time, "duration": item.duration,
            "status": item.status, "prompt_tokens": item.prompt_tokens,
            "completion_tokens": item.completion_tokens, "total_tokens": item.total_tokens,
            "metadata": item.metadata_json,
        }

    async def upsert_annotation(self, conversation_id: int, data: AnnotationUpsert, current_user: User) -> ConversationAnnotation:
        await self.get_conversation(conversation_id)
        annotation = await self.annotation_repo.get_for_conversation(conversation_id)
        tags = list(dict.fromkeys(tag.strip() for tag in data.tags if tag.strip()))
        if annotation:
            annotation.rating = data.rating
            annotation.tags = tags
            annotation.notes = data.notes.strip() if data.notes else None
            annotation.annotator = current_user
            annotation.annotated_at = datetime.now()
            return await self.annotation_repo.update(annotation)
        return await self.annotation_repo.create(ConversationAnnotation(
            conversation_id=conversation_id,
            rating=data.rating,
            tags=tags,
            notes=data.notes.strip() if data.notes else None,
            annotator=current_user,
        ))

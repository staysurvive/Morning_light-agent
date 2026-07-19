import json
from datetime import date, datetime, time, timedelta
from typing import Literal

from fastapi import APIRouter, Depends, Query
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.base_schema import PageResult, ResponseSchema
from src.core.deps import require_permission
from src.core.permissions import (
    CONVERSATION_ANNOTATE, CONVERSATION_CREATE, CONVERSATION_DELETE,
    CONVERSATION_EXPORT, CONVERSATION_READ, CONVERSATION_UPDATE,
)
from src.infra.database import get_db
from src.modules.conversation.schema import (
    AnnotationRead, AnnotationUpsert, ConversationCreate, ConversationRead, ConversationUpdate,
    TraceCreate, TraceRead, TurnCreate, TurnRead,
)
from src.modules.conversation.service import ConversationService
from src.modules.user.model import User

router = APIRouter(tags=["Conversation"])


def get_conversation_service(db: AsyncSession = Depends(get_db, scope="function")) -> ConversationService:
    return ConversationService(db)


@router.get("/conversations", response_model=ResponseSchema[PageResult[ConversationRead]], dependencies=[Depends(require_permission(CONVERSATION_READ))])
async def list_conversations(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    keyword: str | None = Query(default=None),
    agent_id: int | None = Query(default=None, ge=1),
    user_id: int | None = Query(default=None, ge=1),
    status: Literal["active", "completed", "failed"] | None = Query(default=None),
    start_date: date | None = Query(default=None),
    end_date: date | None = Query(default=None),
    service: ConversationService = Depends(get_conversation_service),
):
    start_at = datetime.combine(start_date, time.min) if start_date else None
    end_at = datetime.combine(end_date + timedelta(days=1), time.min) if end_date else None
    if start_date and end_date and end_date < start_date:
        from src.core.exceptions import BizException
        raise BizException(code=400, message="结束日期不能早于开始日期")
    items, total = await service.search_page(
        (page - 1) * page_size, page_size, keyword, agent_id, user_id, status, start_at, end_at
    )
    return ResponseSchema(data=PageResult(
        items=[ConversationRead.model_validate(item) for item in items], total=total,
        page=page, page_size=page_size,
    ))


@router.post("/conversations", response_model=ResponseSchema[ConversationRead])
async def create_conversation(
    data: ConversationCreate,
    current_user: User = Depends(require_permission(CONVERSATION_CREATE)),
    service: ConversationService = Depends(get_conversation_service),
):
    return ResponseSchema(data=ConversationRead.model_validate(
        await service.create_conversation(data, current_user)
    ))


@router.get("/conversations/{conversation_id}", response_model=ResponseSchema[ConversationRead], dependencies=[Depends(require_permission(CONVERSATION_READ))])
async def get_conversation(conversation_id: int, service: ConversationService = Depends(get_conversation_service)):
    return ResponseSchema(data=ConversationRead.model_validate(await service.get_conversation(conversation_id)))


@router.put("/conversations/{conversation_id}", response_model=ResponseSchema[ConversationRead], dependencies=[Depends(require_permission(CONVERSATION_UPDATE))])
async def update_conversation(conversation_id: int, data: ConversationUpdate, service: ConversationService = Depends(get_conversation_service)):
    return ResponseSchema(data=ConversationRead.model_validate(
        await service.update_conversation(conversation_id, data)
    ))


@router.delete("/conversations/{conversation_id}", response_model=ResponseSchema[None], dependencies=[Depends(require_permission(CONVERSATION_DELETE))])
async def delete_conversation(conversation_id: int, service: ConversationService = Depends(get_conversation_service)):
    await service.delete_conversation(conversation_id)
    return ResponseSchema(data=None)


@router.post("/conversations/{conversation_id}/turns", response_model=ResponseSchema[TurnRead], dependencies=[Depends(require_permission(CONVERSATION_CREATE))])
async def add_turn(conversation_id: int, data: TurnCreate, service: ConversationService = Depends(get_conversation_service)):
    return ResponseSchema(data=TurnRead.model_validate(await service.add_turn(conversation_id, data)))


@router.get("/conversations/{conversation_id}/turns", response_model=ResponseSchema[list[TurnRead]], dependencies=[Depends(require_permission(CONVERSATION_READ))])
async def list_turns(conversation_id: int, service: ConversationService = Depends(get_conversation_service)):
    return ResponseSchema(data=[TurnRead.model_validate(item) for item in await service.list_turns(conversation_id)])


@router.post("/turns/{turn_id}/trace", response_model=ResponseSchema[TraceRead], dependencies=[Depends(require_permission(CONVERSATION_CREATE))])
async def add_trace(turn_id: int, data: TraceCreate, service: ConversationService = Depends(get_conversation_service)):
    item = await service.add_trace(turn_id, data)
    return ResponseSchema(data=TraceRead.model_validate(service.serialize_trace(item)))


@router.get("/turns/{turn_id}/trace", response_model=ResponseSchema[list[TraceRead]], dependencies=[Depends(require_permission(CONVERSATION_READ))])
async def list_trace(turn_id: int, service: ConversationService = Depends(get_conversation_service)):
    return ResponseSchema(data=[
        TraceRead.model_validate(service.serialize_trace(item)) for item in await service.list_trace(turn_id)
    ])


@router.put("/conversations/{conversation_id}/annotation", response_model=ResponseSchema[AnnotationRead])
async def upsert_annotation(
    conversation_id: int,
    data: AnnotationUpsert,
    current_user: User = Depends(require_permission(CONVERSATION_ANNOTATE)),
    service: ConversationService = Depends(get_conversation_service),
):
    return ResponseSchema(data=AnnotationRead.model_validate(
        await service.upsert_annotation(conversation_id, data, current_user)
    ))


@router.get("/conversations/{conversation_id}/export", dependencies=[Depends(require_permission(CONVERSATION_EXPORT))])
async def export_conversation(
    conversation_id: int,
    format: Literal["json", "txt"] = Query(default="json"),
    service: ConversationService = Depends(get_conversation_service),
):
    conversation = ConversationRead.model_validate(await service.get_conversation(conversation_id))
    turns = [TurnRead.model_validate(item) for item in await service.list_turns(conversation_id)]
    filename = f"conversation-{conversation_id}.{format}"
    if format == "txt":
        lines = [
            f"Conversation ID: {conversation.id}", f"Agent: {conversation.agent_name}",
            f"User: {conversation.user_name}", f"Started at: {conversation.started_at.isoformat()}", "",
        ]
        for turn in turns:
            lines.extend([f"[{turn.role}] {turn.timestamp.isoformat()}", turn.content, ""])
        content = "\n".join(lines).encode("utf-8")
        media_type = "text/plain; charset=utf-8"
    else:
        payload = {
            "conversation": conversation.model_dump(mode="json"),
            "turns": [item.model_dump(mode="json") for item in turns],
        }
        content = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
        media_type = "application/json"
    return Response(
        content=content, media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )

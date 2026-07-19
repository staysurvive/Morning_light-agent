from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.base_schema import PageResult, ResponseSchema
from src.core.deps import PageParams, require_permission
from src.core.permissions import AGENT_CREATE, AGENT_DELETE, AGENT_PUBLISH, AGENT_READ, AGENT_START_STOP, AGENT_UPDATE
from src.infra.database import get_db
from src.modules.agent.schema import (
    AgentCreate,
    AgentPublishRequest,
    AgentRead,
    AgentRollbackRequest,
    AgentUpdate,
    AgentVersionRead,
)
from src.modules.agent.service import AgentService
from src.modules.user.model import User

router = APIRouter(prefix="/agents", tags=["Agent"])


def get_agent_service(db: AsyncSession = Depends(get_db, scope="function")) -> AgentService:
    return AgentService(db)


@router.get("", response_model=ResponseSchema[PageResult[AgentRead]], dependencies=[Depends(require_permission(AGENT_READ))])
async def list_agents(params: PageParams = Depends(), service: AgentService = Depends(get_agent_service)):
    items, total = await service.search_page(params.offset, params.page_size, params.keyword)
    return ResponseSchema(data=PageResult(
        items=[AgentRead.model_validate(item) for item in items],
        total=total,
        page=params.page,
        page_size=params.page_size,
    ))


@router.post("", response_model=ResponseSchema[AgentRead])
async def create_agent(
    data: AgentCreate,
    current_user: User = Depends(require_permission(AGENT_CREATE)),
    service: AgentService = Depends(get_agent_service),
):
    return ResponseSchema(data=AgentRead.model_validate(await service.create_agent(data, current_user)))


@router.get("/{agent_id}", response_model=ResponseSchema[AgentRead], dependencies=[Depends(require_permission(AGENT_READ))])
async def get_agent(agent_id: int, service: AgentService = Depends(get_agent_service)):
    return ResponseSchema(data=AgentRead.model_validate(await service.get_agent(agent_id)))


@router.put("/{agent_id}", response_model=ResponseSchema[AgentRead], dependencies=[Depends(require_permission(AGENT_UPDATE))])
async def update_agent(agent_id: int, data: AgentUpdate, service: AgentService = Depends(get_agent_service)):
    return ResponseSchema(data=AgentRead.model_validate(await service.update_agent(agent_id, data)))


@router.delete("/{agent_id}", response_model=ResponseSchema[None], dependencies=[Depends(require_permission(AGENT_DELETE))])
async def delete_agent(agent_id: int, service: AgentService = Depends(get_agent_service)):
    await service.delete_agent(agent_id)
    return ResponseSchema(data=None)


@router.post("/{agent_id}/publish", response_model=ResponseSchema[AgentRead])
async def publish_agent(
    agent_id: int,
    data: AgentPublishRequest,
    current_user: User = Depends(require_permission(AGENT_PUBLISH)),
    service: AgentService = Depends(get_agent_service),
):
    return ResponseSchema(data=AgentRead.model_validate(
        await service.publish_agent(agent_id, data.changelog, current_user)
    ))


@router.get("/{agent_id}/versions", response_model=ResponseSchema[list[AgentVersionRead]], dependencies=[Depends(require_permission(AGENT_READ))])
async def list_agent_versions(agent_id: int, service: AgentService = Depends(get_agent_service)):
    versions = await service.list_versions(agent_id)
    return ResponseSchema(data=[AgentVersionRead.model_validate(item) for item in versions])


@router.post("/{agent_id}/rollback", response_model=ResponseSchema[AgentRead])
async def rollback_agent(
    agent_id: int,
    data: AgentRollbackRequest,
    current_user: User = Depends(require_permission(AGENT_PUBLISH)),
    service: AgentService = Depends(get_agent_service),
):
    return ResponseSchema(data=AgentRead.model_validate(
        await service.rollback_agent(agent_id, data.version, current_user)
    ))


@router.post("/{agent_id}/start", response_model=ResponseSchema[AgentRead], dependencies=[Depends(require_permission(AGENT_START_STOP))])
async def start_agent(agent_id: int, service: AgentService = Depends(get_agent_service)):
    return ResponseSchema(data=AgentRead.model_validate(await service.start_agent(agent_id)))


@router.post("/{agent_id}/stop", response_model=ResponseSchema[AgentRead], dependencies=[Depends(require_permission(AGENT_START_STOP))])
async def stop_agent(agent_id: int, service: AgentService = Depends(get_agent_service)):
    return ResponseSchema(data=AgentRead.model_validate(await service.stop_agent(agent_id)))

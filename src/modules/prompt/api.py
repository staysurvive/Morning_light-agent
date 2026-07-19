from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.base_schema import PageResult, ResponseSchema
from src.core.deps import PageParams, require_permission
from src.core.permissions import PROMPT_CREATE, PROMPT_DELETE, PROMPT_PUBLISH, PROMPT_READ, PROMPT_UPDATE
from src.infra.database import get_db
from src.modules.prompt.schema import (
    PromptCreate,
    PromptPublishRequest,
    PromptRead,
    PromptRollbackRequest,
    PromptUpdate,
    PromptVersionRead,
)
from src.modules.prompt.service import PromptService
from src.modules.user.model import User

router = APIRouter(prefix="/prompts", tags=["Prompt"])


def get_prompt_service(db: AsyncSession = Depends(get_db, scope="function")) -> PromptService:
    return PromptService(db)


@router.get("", response_model=ResponseSchema[PageResult[PromptRead]], dependencies=[Depends(require_permission(PROMPT_READ))])
async def list_prompts(params: PageParams = Depends(), service: PromptService = Depends(get_prompt_service)):
    items, total = await service.search_page(params.offset, params.page_size, params.keyword)
    return ResponseSchema(data=PageResult(
        items=[PromptRead.model_validate(item) for item in items],
        total=total,
        page=params.page,
        page_size=params.page_size,
    ))


@router.post("", response_model=ResponseSchema[PromptRead])
async def create_prompt(
    data: PromptCreate,
    current_user: User = Depends(require_permission(PROMPT_CREATE)),
    service: PromptService = Depends(get_prompt_service),
):
    return ResponseSchema(data=PromptRead.model_validate(await service.create_prompt(data, current_user)))


@router.get("/{prompt_id}", response_model=ResponseSchema[PromptRead], dependencies=[Depends(require_permission(PROMPT_READ))])
async def get_prompt(prompt_id: int, service: PromptService = Depends(get_prompt_service)):
    return ResponseSchema(data=PromptRead.model_validate(await service.get_prompt(prompt_id)))


@router.put("/{prompt_id}", response_model=ResponseSchema[PromptRead], dependencies=[Depends(require_permission(PROMPT_UPDATE))])
async def update_prompt(prompt_id: int, data: PromptUpdate, service: PromptService = Depends(get_prompt_service)):
    return ResponseSchema(data=PromptRead.model_validate(await service.update_prompt(prompt_id, data)))


@router.delete("/{prompt_id}", response_model=ResponseSchema[None], dependencies=[Depends(require_permission(PROMPT_DELETE))])
async def delete_prompt(prompt_id: int, service: PromptService = Depends(get_prompt_service)):
    await service.delete_prompt(prompt_id)
    return ResponseSchema(data=None)


@router.post("/{prompt_id}/publish", response_model=ResponseSchema[PromptRead])
async def publish_prompt(
    prompt_id: int,
    data: PromptPublishRequest,
    current_user: User = Depends(require_permission(PROMPT_PUBLISH)),
    service: PromptService = Depends(get_prompt_service),
):
    return ResponseSchema(data=PromptRead.model_validate(
        await service.publish_prompt(prompt_id, data.changelog, current_user)
    ))


@router.get("/{prompt_id}/versions", response_model=ResponseSchema[list[PromptVersionRead]], dependencies=[Depends(require_permission(PROMPT_READ))])
async def list_prompt_versions(prompt_id: int, service: PromptService = Depends(get_prompt_service)):
    versions = await service.list_versions(prompt_id)
    return ResponseSchema(data=[PromptVersionRead.model_validate(item) for item in versions])


@router.post("/{prompt_id}/rollback", response_model=ResponseSchema[PromptRead])
async def rollback_prompt(
    prompt_id: int,
    data: PromptRollbackRequest,
    current_user: User = Depends(require_permission(PROMPT_PUBLISH)),
    service: PromptService = Depends(get_prompt_service),
):
    return ResponseSchema(data=PromptRead.model_validate(
        await service.rollback_prompt(prompt_id, data.version, current_user)
    ))

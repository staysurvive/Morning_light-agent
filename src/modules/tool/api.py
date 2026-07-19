from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.base_schema import PageResult, ResponseSchema
from src.core.deps import PageParams, require_permission
from src.core.permissions import TOOL_CREATE, TOOL_DELETE, TOOL_ENABLE, TOOL_READ, TOOL_TEST, TOOL_UPDATE
from src.infra.database import get_db
from src.modules.tool.schema import ToolCreate, ToolRead, ToolTestRequest, ToolTestResult, ToolUpdate
from src.modules.tool.service import ToolService
from src.modules.user.model import User

router = APIRouter(prefix="/tools", tags=["Tool"])


def get_tool_service(db: AsyncSession = Depends(get_db, scope="function")) -> ToolService:
    return ToolService(db)


@router.get("", response_model=ResponseSchema[PageResult[ToolRead]], dependencies=[Depends(require_permission(TOOL_READ))])
async def list_tools(params: PageParams = Depends(), service: ToolService = Depends(get_tool_service)):
    items, total = await service.search_page(params.offset, params.page_size, params.keyword)
    return ResponseSchema(data=PageResult(
        items=[ToolRead.model_validate(service.serialize(item)) for item in items], total=total,
        page=params.page, page_size=params.page_size,
    ))


@router.post("", response_model=ResponseSchema[ToolRead])
async def create_tool(
    data: ToolCreate,
    current_user: User = Depends(require_permission(TOOL_CREATE)),
    service: ToolService = Depends(get_tool_service),
):
    tool = await service.create_tool(data, current_user)
    return ResponseSchema(data=ToolRead.model_validate(service.serialize(tool)))


@router.get("/{tool_id}", response_model=ResponseSchema[ToolRead], dependencies=[Depends(require_permission(TOOL_READ))])
async def get_tool(tool_id: int, service: ToolService = Depends(get_tool_service)):
    tool = await service.get_tool(tool_id)
    return ResponseSchema(data=ToolRead.model_validate(service.serialize(tool)))


@router.put("/{tool_id}", response_model=ResponseSchema[ToolRead], dependencies=[Depends(require_permission(TOOL_UPDATE))])
async def update_tool(tool_id: int, data: ToolUpdate, service: ToolService = Depends(get_tool_service)):
    tool = await service.update_tool(tool_id, data)
    return ResponseSchema(data=ToolRead.model_validate(service.serialize(tool)))


@router.delete("/{tool_id}", response_model=ResponseSchema[None], dependencies=[Depends(require_permission(TOOL_DELETE))])
async def delete_tool(tool_id: int, service: ToolService = Depends(get_tool_service)):
    await service.delete_tool(tool_id)
    return ResponseSchema(data=None)


@router.post("/{tool_id}/enable", response_model=ResponseSchema[ToolRead], dependencies=[Depends(require_permission(TOOL_ENABLE))])
async def enable_tool(tool_id: int, service: ToolService = Depends(get_tool_service)):
    tool = await service.set_enabled(tool_id, True)
    return ResponseSchema(data=ToolRead.model_validate(service.serialize(tool)))


@router.post("/{tool_id}/disable", response_model=ResponseSchema[ToolRead], dependencies=[Depends(require_permission(TOOL_ENABLE))])
async def disable_tool(tool_id: int, service: ToolService = Depends(get_tool_service)):
    tool = await service.set_enabled(tool_id, False)
    return ResponseSchema(data=ToolRead.model_validate(service.serialize(tool)))


@router.post("/{tool_id}/test", response_model=ResponseSchema[ToolTestResult], dependencies=[Depends(require_permission(TOOL_TEST))])
async def test_tool(tool_id: int, data: ToolTestRequest, service: ToolService = Depends(get_tool_service)):
    return ResponseSchema(data=await service.test_tool(tool_id, data.input))

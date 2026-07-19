from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.base_schema import PageResult, ResponseSchema
from src.core.deps import PageParams, require_permission
from src.core.permissions import (
    PERMISSION_CREATE,
    PERMISSION_DELETE,
    PERMISSION_READ,
    PERMISSION_UPDATE,
)
from src.infra.database import get_db
from src.modules.permission.schema import PermissionCreate, PermissionRead, PermissionUpdate
from src.modules.permission.service import PermissionService

router = APIRouter(prefix="/permissions", tags=["Permission"])

def get_permission_service(db: AsyncSession = Depends(get_db, scope="function")) -> PermissionService:
    return PermissionService(db)

# GET /api/v1/permissions/search 分页获取权限
@router.get("/search", response_model=ResponseSchema[PageResult[PermissionRead]], summary="分页搜索权限",
            dependencies=[Depends(require_permission(PERMISSION_READ))])
async def list_search_results(svc: PermissionService = Depends(get_permission_service),
                              params: PageParams = Depends()):
    """分页搜索权限"""
    perms, total_count = await svc.search_page(params.offset, params.page_size, params.keyword)

    # 列表推导式
    perms = [PermissionRead.model_validate(p) for p in perms]

    return ResponseSchema(data=PageResult(
        items=perms,
        total=total_count,
        page=params.page,
        page_size=params.page_size,
    ))


@router.get("/{permission_id}", response_model=ResponseSchema[PermissionRead], summary="根据 ID 获取权限详情",
            dependencies=[Depends(require_permission(PERMISSION_READ))])
async def get_permission(permission_id: int, service: PermissionService = Depends(get_permission_service)):
    """根据 ID 获取权限"""
    permission = await service.get_permission(permission_id)
    return ResponseSchema(data=PermissionRead.model_validate(permission))

@router.get("/", response_model=ResponseSchema[list[PermissionRead]], summary="获取所有权限列表",
            dependencies=[Depends(require_permission(PERMISSION_READ))])
async def list_permissions(service: PermissionService = Depends(get_permission_service)):
    """获取所有权限"""
    permissions = await service.list_permissions()
    return ResponseSchema(data=[PermissionRead.model_validate(p) for p in permissions])

@router.post("/", response_model=ResponseSchema[PermissionRead], summary="创建权限",
             dependencies=[Depends(require_permission(PERMISSION_CREATE))])
async def create_permission(data: PermissionCreate,
service: PermissionService = Depends(get_permission_service)):
    """创建权限"""
    permission = await service.create_permission(data)
    return ResponseSchema(data=PermissionRead.model_validate(permission))

@router.put("/{permission_id}", response_model=ResponseSchema[PermissionRead], summary="更新权限",
            dependencies=[Depends(require_permission(PERMISSION_UPDATE))])
async def update_permission(permission_id: int, data: PermissionUpdate,
service: PermissionService = Depends(get_permission_service)):
    """更新权限"""
    permission = await service.update_permission(permission_id, data)
    return ResponseSchema(data=PermissionRead.model_validate(permission))

@router.delete("/{permission_id}", response_model=ResponseSchema[None], summary="删除权限",
               dependencies=[Depends(require_permission(PERMISSION_DELETE))])
async def delete_permission(permission_id: int,
service: PermissionService = Depends(get_permission_service)):
    """删除权限"""
    await service.delete_permission(permission_id)
    return ResponseSchema(data=None)


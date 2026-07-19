from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from src.infra.database import get_db
from src.core.base_schema import ResponseSchema, PageResult
from src.modules.user.schema import UserAssignRoles, UserCreate, UserRead, UserWithRolesRead
from src.modules.user.service import UserService
from src.core.deps import get_current_user, PageParams, require_permission
from src.core.permissions import (
    USER_ASSIGN_ROLES,
    USER_CREATE,
    USER_DELETE,
    USER_READ,
)
from src.modules.user.model import User

router = APIRouter(prefix="/users", tags=["User"])


def get_user_service(db: AsyncSession = Depends(get_db, scope="function")) -> UserService:
    return UserService(db)


@router.post(
    "",
    response_model=ResponseSchema[UserRead],
    dependencies=[Depends(require_permission(USER_CREATE))],
)
async def create_user(
    data: UserCreate,
    svc: UserService = Depends(get_user_service),
):
    user = await svc.create_user(data)
    return ResponseSchema(data=UserRead.model_validate(user))


@router.get("/me", response_model=ResponseSchema[UserWithRolesRead])
async def get_me(current_user: User = Depends(get_current_user)):
    """获取当前登录用户信息（需要 token）"""
    return ResponseSchema(data=UserWithRolesRead.model_validate(current_user))


@router.get(
    "/search",
    response_model=ResponseSchema[PageResult[UserRead]],
    summary="分页搜索用户",
    dependencies=[Depends(require_permission(USER_READ))],
)
async def list_search_results(
    svc: UserService = Depends(get_user_service),
    params: PageParams = Depends(),
):
    users, total_count = await svc.search_page(
        params.offset,
        params.page_size,
        params.keyword,
    )
    return ResponseSchema(data=PageResult(
        items=[UserRead.model_validate(user) for user in users],
        total=total_count,
        page=params.page,
        page_size=params.page_size,
    ))


@router.get(
    "/{user_id}",
    response_model=ResponseSchema[UserWithRolesRead],
    dependencies=[Depends(require_permission(USER_READ))],
)
async def get_user(
    user_id: int,
    svc: UserService = Depends(get_user_service),
):
    user = await svc.get_user(user_id)
    return ResponseSchema(data=UserWithRolesRead.model_validate(user))


@router.delete(
    "/{user_id}",
    response_model=ResponseSchema[None],
    summary="删除用户",
    dependencies=[Depends(require_permission(USER_DELETE))],
)
async def delete_user(
    user_id: int,
    svc: UserService = Depends(get_user_service),
):
    await svc.delete_user(user_id)
    return ResponseSchema[None](data=None)


@router.get(
    "",
    response_model=ResponseSchema[list[UserRead]],
    dependencies=[Depends(require_permission(USER_READ))],
)
async def list_users(
    offset: int = 0,
    limit: int = 100,
    svc: UserService = Depends(get_user_service),
):
    users = await svc.list_users(offset, limit)
    return ResponseSchema(data=[UserRead.model_validate(u) for u in users])


#  PUT   /api/v1/users/{user_id}/roles   给用户分配角色
@router.put(
    "/{user_id}/roles",
    response_model=ResponseSchema[UserWithRolesRead],
    summary="给用户分配角色",
    dependencies=[Depends(require_permission(USER_ASSIGN_ROLES))],
)
async def assign_roles_to_user(
    user_id: int,
    data: UserAssignRoles,
    svc: UserService = Depends(get_user_service),
):
    user = await svc.assign_roles(user_id, data.role_ids)
    return ResponseSchema(data=UserWithRolesRead.model_validate(user))


#  GET   /api/v1/users/{user_id}/roles   查看用户的角色列表
@router.get(
    "/{user_id}/roles",
    response_model=ResponseSchema[list[UserWithRolesRead]],
    summary="查看用户的角色列表",
    dependencies=[Depends(require_permission(USER_READ))],
)
async def get_user_roles(
    user_id: int,
    svc: UserService = Depends(get_user_service),
):
    user = await svc.get_user_with_roles(user_id)
    return ResponseSchema(data=[UserWithRolesRead.model_validate(user)])



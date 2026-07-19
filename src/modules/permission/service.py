from math import perm

from pydantic_settings.sources.providers import aws

from src.core.exceptions import ERROR_PERM_NOT_FOUND, ERROR_PERM_NOT_FOUND_MSG
from src.core.exceptions import BizException
from src.infra.database import AsyncSession
from src.modules.permission.model import Permission
from src.modules.permission.repository import PermissionRepository
from src.modules.permission.schema import PermissionCreate, PermissionUpdate

class PermissionService:
    def __init__(self, db: AsyncSession):
        self.repo = PermissionRepository(db)

    async def create_permission(self, data: PermissionCreate) -> Permission:
        # 1. 检查 code 是否已存在，已存在则抛 BizException
        perm = await self.repo.get_by_code(data.code)
        if perm:
            raise BizException(code=3001, message="Permission already exists")

        # 2. 创建 Permission 对象
        perm = Permission(code=data.code, name=data.name, description=data.description)

        # 3. 调用 repo.create() 保存; 数据库保存完后，perm对象中还会有 id 字段
        return await self.repo.create(perm)

    async def get_permission(self, permission_id: int) -> Permission:
        perm = await self.repo.get_by_id(permission_id)
        if  not perm:
            raise BizException(code=ERROR_PERM_NOT_FOUND, message=ERROR_PERM_NOT_FOUND_MSG)
        return perm

    async def list_permissions(self) -> list[Permission]:
        perm = await self.repo.get_all(0,10000)
        return perm

    async def update_permission(self, permission_id: int, data: PermissionUpdate) -> Permission:
        # 1. 查找权限，不存在抛异常
        perm = await self.get_permission(permission_id)
        # 2. 只更新 data 中非 None 的字段
        if data.name:
            perm.name = data.name
        if data.description:
            perm.description = data.description
        # 3. 调用 repo.update()
        return await self.repo.update(perm)

    async def delete_permission(self, permission_id: int) -> None:
        self.repo.delete_by_id(permission_id)

    async def search_page(self, offset: int, limit: int,keyword: str| None) -> tuple[list[Permission], int]:
        return await self.repo.search_page(offset, limit, keyword)
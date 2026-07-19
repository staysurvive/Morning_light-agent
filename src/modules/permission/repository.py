from src.core.base_repository import BaseRepository
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.modules.permission.model import Permission

class PermissionRepository(BaseRepository[Permission]):
    SEARCH_FIELDS = ["code","name"]

    def __init__(self, db: AsyncSession):
        super().__init__(Permission, db)

    # 按照权限码查找权限的功能
    async def get_by_code(self,code:str) -> Permission | None:
        stmt = select(Permission).where(Permission.code == code)
        result = await  self.db.scalar(stmt)
        return result

    async def get_by_ids(self, ids: list[int]) -> list[Permission]:
        stmt = select(Permission).where(Permission.id.in_(ids))
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def get_by_id(self, id: int) -> Permission | None:
        return await super().get_by_id(id)
    # 分页搜索
    async def search_page(self, offset: int, limit: int, keyword: str | None) -> tuple[list[Permission], int]:
        return await  self.get_page(offset,limit,keyword,self.SEARCH_FIELDS)

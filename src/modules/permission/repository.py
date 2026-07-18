from sqlalchemy.engine import result

from src.core.base_repository import BaseRepository
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.modules.permission.model import Permission

class PermissionRepository(BaseRepository[Permission]):
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

    async def get_by_id(self,ids:list[int]) -> list[Permission]:
        result =  await self.db.scalar(select(Permission).where(Permission.id.in_(ids)))
        return result.all()

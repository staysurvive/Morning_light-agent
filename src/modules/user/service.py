# service 负责做业务逻辑 ， 与数据库交互
from sqlalchemy.ext.asyncio import AsyncSession
from src.core.exceptions import BizException
from src.modules.user.model import User
from src.modules.user.schema import UserCreate
from src.modules.user.repository import UserRepository
from src.modules.utils.password_utils import hash_password
from src.modules.role.repository import RoleRepository



class UserService:
    def __init__(self, db: AsyncSession):
        self.repo = UserRepository(db)
        self.role_repo = RoleRepository(db)

    async def create_user(self, data: UserCreate) -> User:
        if await self.repo.get_by_username(data.username):
            raise BizException(code=400, message="用户名已存在")
        if await self.repo.get_by_email(data.email):
            raise BizException(code=400, message="邮箱已存在")

        user = User(
            username=data.username,
            email=data.email,
            hashed_password=hash_password(data.password),  # 项目开发时用 bcrypt 等加密
        )
        return await self.repo.create(user)

    async def get_user(self, user_id: int) -> User:
        user = await self.repo.get_by_id(user_id)
        if not user:
            raise BizException(code=404, message="用户不存在")
        return user

    async def list_users(self, offset: int = 0, limit: int = 100):
        return await self.repo.get_all(offset=offset, limit=limit)

    async def delete_user(self, user_id: int) -> None:
        if not await self.repo.delete_by_id(user_id):
            raise BizException(code=404, message="用户不存在")

    async def assign_roles(self, user_id: int, role_ids: list[int]) -> User:
        # 1. 查找用户，不存在抛异常
        user = await self.get_user(user_id)
        if not user:
            raise BizException(code=30001, message="用户不存在")
        # 2. 通过 RoleRepository.get_by_ids(role_ids) 批量查询角色
        role_list = await self.role_repo.get_by_ids(role_ids)
        # 3. 校验数量是否匹配
        if len(role_list) != len(role_ids):
            raise BizException(code=400, message="角色不存在")
        # 4. user.roles = role_list（整体替换）
        user.roles = role_list
        # 5. flush + refresh
        await self.repo.update(user)
        # 6. 返回 user
        return user

    async def get_user_with_roles(self, user_id: int) -> User:
    # 和 get_user 一样，但返回的 User 对象会自动带上 roles
        user = await self.get_user(user_id)
    # 因为 User.roles 设置了 lazy="selectin"，所以不需要额外操作
    #     user.roles   如果懒加载，一下，触发数据库查询即可
    # 直接复用 get_user 即可
        return user


    async def search_page(self, offset: int, limit: int,keyword: str| None) -> tuple[list[User], int]:
        return await self.repo.search_page(offset, limit, keyword)

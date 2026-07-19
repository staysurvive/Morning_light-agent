from collections.abc import Awaitable, Callable

from fastapi import Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from src.infra.database import get_db
from src.core.exceptions import BizException
from src.modules.utils.jwt_utils import verify_jwt, oauth2_scheme
from src.modules.user.model import User

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db, scope="function"),
) -> User:
    """从 JWT token 中解析当前登录用户，用于保护接口"""
    try:
        payload = verify_jwt(token)
        user_id = int(payload.get("sub"))
    except Exception:
        raise BizException(code=401, message="未登录或 token 已过期")

    user = await db.get(User, user_id)
    if not user:
        raise BizException(code=401, message="用户不存在")
    if not user.is_active:
        raise BizException(code=401, message="账号已被禁用")

    return user


def user_has_permission(user: User, permission_code: str) -> bool:
    if user.is_superuser:
        return True
    return any(
        permission.code == permission_code
        for role in user.roles
        for permission in role.permissions
    )


def require_permission(permission_code: str) -> Callable[..., Awaitable[User]]:
    async def permission_dependency(
        current_user: User = Depends(get_current_user),
    ) -> User:
        if not user_has_permission(current_user, permission_code):
            raise BizException(
                code=403,
                message=f"权限不足，需要权限：{permission_code}",
            )
        return current_user

    return permission_dependency

# api/vi/users?page=1&page_size=10&keyword=张三
#
class PageParams:
    """通用分页参数，通过 Depends 注入到接口中"""
    def __init__(
        self,
        page: int = Query(1, ge=1, description="页码，从1开始"),
        page_size: int = Query(10, ge=1, le=100, description="每页条数"),
        keyword: str | None = Query(None, description="搜索关键词"),
    ):
        self.page = page
        self.page_size = page_size
        self.keyword = keyword

# 动态计算 offset
    @property
    def offset(self) -> int:
        """计算 SQL OFFSET"""
        return (self.page - 1) * self.page_size

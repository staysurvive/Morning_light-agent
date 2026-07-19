from types import SimpleNamespace

import pytest

from src.core.deps import require_permission, user_has_permission
from src.core.exceptions import BizException


def make_user(*permission_codes: str, is_superuser: bool = False):
    permissions = [SimpleNamespace(code=code) for code in permission_codes]
    role = SimpleNamespace(permissions=permissions)
    return SimpleNamespace(is_superuser=is_superuser, roles=[role])


def test_user_has_permission_from_assigned_role():
    user = make_user("user_create")

    assert user_has_permission(user, "user_create") is True
    assert user_has_permission(user, "user_delete") is False


def test_superuser_bypasses_permission_catalog():
    user = make_user(is_superuser=True)

    assert user_has_permission(user, "permission_not_seeded") is True


@pytest.mark.asyncio
async def test_require_permission_rejects_user_without_permission():
    dependency = require_permission("user_create")

    with pytest.raises(BizException) as caught:
        await dependency(make_user())

    assert caught.value.code == 403
    assert caught.value.message == "权限不足，需要权限：user_create"


@pytest.mark.asyncio
async def test_require_permission_accepts_assigned_permission():
    dependency = require_permission("user_create")
    user = make_user("user_create")

    assert await dependency(user) is user

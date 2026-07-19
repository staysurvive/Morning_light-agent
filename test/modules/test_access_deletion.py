from unittest.mock import AsyncMock

import pytest

from src.core.base_repository import BaseRepository
from src.core.exceptions import BizException
from src.modules.permission.service import PermissionService
from src.modules.role.service import RoleService
from src.modules.user.model import User
from src.modules.user.service import UserService


@pytest.mark.asyncio
async def test_base_repository_delete_by_id_deletes_existing_entity():
    entity = object()
    db = AsyncMock()
    db.get.return_value = entity
    repo = BaseRepository(User, db)

    deleted = await repo.delete_by_id(7)

    assert deleted is True
    db.get.assert_awaited_once_with(User, 7)
    db.delete.assert_awaited_once_with(entity)
    db.flush.assert_awaited_once()


@pytest.mark.asyncio
async def test_base_repository_delete_by_id_reports_missing_entity():
    db = AsyncMock()
    db.get.return_value = None
    repo = BaseRepository(User, db)

    deleted = await repo.delete_by_id(404)

    assert deleted is False
    db.delete.assert_not_awaited()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("service_type", "resource_id", "message"),
    [
        (UserService, 11, "用户不存在"),
        (RoleService, 12, "角色 12 不存在"),
        (PermissionService, 13, "权限不存在"),
    ],
)
async def test_delete_rejects_missing_resource(service_type, resource_id, message):
    service = service_type(AsyncMock())
    service.repo = AsyncMock()
    service.repo.delete_by_id.return_value = False
    method = getattr(service, f"delete_{service_type.__name__.removesuffix('Service').lower()}")

    with pytest.raises(BizException) as caught:
        await method(resource_id)

    assert caught.value.code == 404
    assert caught.value.message == message


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("service_type", "resource_id"),
    [(UserService, 21), (RoleService, 22), (PermissionService, 23)],
)
async def test_delete_accepts_existing_resource(service_type, resource_id):
    service = service_type(AsyncMock())
    service.repo = AsyncMock()
    service.repo.delete_by_id.return_value = True
    method = getattr(service, f"delete_{service_type.__name__.removesuffix('Service').lower()}")

    await method(resource_id)

    service.repo.delete_by_id.assert_awaited_once_with(resource_id)

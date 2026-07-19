"""seed_rbac_permissions

Revision ID: 66b777046b3a
Revises: a7745ff86f43
Create Date: 2026-07-19 18:41:16.698187

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '66b777046b3a'
down_revision: Union[str, Sequence[str], None] = 'a7745ff86f43'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Seed the permission catalog and grant it to an existing admin role."""
    permissions = sa.table(
        "permissions",
        sa.column("id", sa.BigInteger()),
        sa.column("code", sa.String()),
        sa.column("name", sa.String()),
        sa.column("description", sa.String()),
    )
    roles = sa.table(
        "roles",
        sa.column("id", sa.BigInteger()),
        sa.column("code", sa.String()),
    )
    role_permissions = sa.table(
        "role_permissions",
        sa.column("role_id", sa.BigInteger()),
        sa.column("permission_id", sa.BigInteger()),
    )
    catalog = (
        ("user_read", "查看用户", "查看用户列表、详情和角色"),
        ("user_create", "创建用户", "创建平台用户"),
        ("user_delete", "删除用户", "删除平台用户"),
        ("user_assign_roles", "分配用户角色", "调整用户拥有的角色"),
        ("role_read", "查看角色", "查看角色列表、详情和权限"),
        ("role_create", "创建角色", "创建平台角色"),
        ("role_update", "更新角色", "修改角色名称和描述"),
        ("role_delete", "删除角色", "删除平台角色"),
        ("role_assign_permissions", "分配角色权限", "调整角色拥有的权限"),
        ("permission_read", "查看权限", "查看权限列表和详情"),
        ("permission_create", "创建权限", "创建权限定义"),
        ("permission_update", "更新权限", "修改权限名称和描述"),
        ("permission_delete", "删除权限", "删除权限定义"),
    )

    connection = op.get_bind()
    existing_codes = set(connection.execute(sa.select(permissions.c.code)).scalars())
    missing = [
        {"code": code, "name": name, "description": description}
        for code, name, description in catalog
        if code not in existing_codes
    ]
    if missing:
        op.bulk_insert(permissions, missing)

    admin_role_id = connection.execute(
        sa.select(roles.c.id).where(roles.c.code == "admin")
    ).scalar_one_or_none()
    if admin_role_id is None:
        return

    catalog_codes = [code for code, _, _ in catalog]
    permission_ids = list(
        connection.execute(
            sa.select(permissions.c.id).where(permissions.c.code.in_(catalog_codes))
        ).scalars()
    )
    assigned_ids = set(
        connection.execute(
            sa.select(role_permissions.c.permission_id).where(
                role_permissions.c.role_id == admin_role_id
            )
        ).scalars()
    )
    assignments = [
        {"role_id": admin_role_id, "permission_id": permission_id}
        for permission_id in permission_ids
        if permission_id not in assigned_ids
    ]
    if assignments:
        op.bulk_insert(role_permissions, assignments)


def downgrade() -> None:
    """Preserve permission data because some codes may predate this migration."""

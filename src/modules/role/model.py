from sqlalchemy import Table, Column, BigInteger, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.modules.permission.model import Permission
from src.core.base_model import Base, BaseModel

role_permissions = Table(
    "role_permissions",
    Base.metadata,
    Column("role_id", BigInteger, ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True),
    Column("permission_id", BigInteger, ForeignKey("permissions.id", ondelete="CASCADE"), primary_key=True),
)

# 角色表： role.premissions 就能拿到角色对应的权限
class Role(BaseModel):
    __tablename__ = "roles"
    code: Mapped[str] = mapped_column(String(100), unique=True, comment="角色编码")
    name: Mapped[str] = mapped_column(String(100),  comment="角色名称")
    description: Mapped[str] = mapped_column(String(200), nullable=True, comment="角色描述")
    permissions: Mapped[list["Permission"]] = relationship(
        "Permission",
        secondary=role_permissions,
        lazy="selectin",  # 立即加载关联权限
        # backref="roles",
    )

user_roles = Table(
    "user_roles",
    Base.metadata,
    Column("user_id", BigInteger, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    Column("role_id", BigInteger, ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True),
)
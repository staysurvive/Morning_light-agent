# 给前端返回的pydantic 数据模型
# schema 表示模式、架构或纲要，在计算机科学中，它通常用于描述定义结构蓝图
from pydantic import BaseModel, EmailStr
from src.modules.role.schema import RoleRead

class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str


class UserRead(BaseModel):
    id: int
    username: str
    email: str 
    is_active: bool  # 是否启用

    # 从 orm 模型中直接映射字段, 而不是手动定义
    model_config = {"from_attributes": True}

class UserWithRolesRead(BaseModel):
    id: int
    username: str
    email: str
    is_active: bool
    roles: list[RoleRead] = []     # 从 role 模块导入 RoleRead
    model_config = {"from_attributes": True}

class UserAssignRoles(BaseModel):
    role_ids: list[int]
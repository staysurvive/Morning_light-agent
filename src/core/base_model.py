from datetime import datetime
from sqlalchemy import BigInteger, DateTime, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

# 希望创建的每个表都有几个默认字段
# 1. id : 主键, 自增, 唯一标识
# 2. created_at : 创建时间, 默认当前时间
# 3. updated_at : 更新时间, 默认当前时间, 更新时自动更新

class Base(DeclarativeBase):
    """所有 Model 继承此类"""
    pass

# 创建时间和更新时间由数据库自动维护
class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), comment="创建时间"
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间"
    )

# 所有的数据表都有 id, created_at, updated_at 字段;
# 所有ORM模型都继承自 BaseModel
class BaseModel(Base, TimestampMixin):
    __abstract__ = True
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
from datetime import datetime
from decimal import Decimal

from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, JSON, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.base_model import BaseModel


class Tool(BaseModel):
    __tablename__ = "tools"

    name: Mapped[str] = mapped_column(String(150), unique=True, index=True, comment="工具名称")
    description: Mapped[str | None] = mapped_column(String(500), nullable=True, comment="工具描述")
    type: Mapped[str] = mapped_column(String(30), index=True, comment="工具类型")
    status: Mapped[str] = mapped_column(String(20), default="disabled", index=True, comment="工具状态")
    config_encrypted: Mapped[str | None] = mapped_column(Text, nullable=True, comment="加密后的工具配置")
    function_definition: Mapped[dict | None] = mapped_column(JSON, nullable=True, comment="函数定义")
    call_count_7d: Mapped[int] = mapped_column(default=0, comment="近 7 日测试/调用次数")
    success_rate: Mapped[Decimal] = mapped_column(Numeric(6, 2), default=0, comment="近 7 日成功率")
    avg_latency: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0, comment="近 7 日平均延迟")
    created_by_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="创建人 ID",
    )

    creator = relationship("User", lazy="selectin")
    executions = relationship(
        "ToolExecution",
        back_populates="tool",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    @property
    def created_by(self) -> str | None:
        return self.creator.username if self.creator else None


class ToolExecution(BaseModel):
    __tablename__ = "tool_executions"

    tool_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("tools.id", ondelete="CASCADE"),
        index=True,
        comment="工具 ID",
    )
    success: Mapped[bool] = mapped_column(Boolean, index=True, comment="是否成功")
    latency_ms: Mapped[int] = mapped_column(default=0, comment="延迟毫秒")
    is_test: Mapped[bool] = mapped_column(Boolean, default=True, index=True, comment="是否测试调用")
    error: Mapped[str | None] = mapped_column(String(1000), nullable=True, comment="错误摘要")
    executed_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, index=True, comment="执行时间")

    tool = relationship("Tool", back_populates="executions")

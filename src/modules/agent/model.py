from datetime import datetime
from decimal import Decimal

from sqlalchemy import JSON, BigInteger, Boolean, DateTime, ForeignKey, Numeric, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.base_model import BaseModel


class Agent(BaseModel):
    __tablename__ = "agents"

    name: Mapped[str] = mapped_column(String(150), unique=True, index=True, comment="Agent 名称")
    description: Mapped[str | None] = mapped_column(String(500), nullable=True, comment="Agent 描述")
    type: Mapped[str] = mapped_column(String(30), index=True, comment="Agent 类型")
    status: Mapped[str] = mapped_column(String(20), default="draft", index=True, comment="运行状态")
    model_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("models.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="模型 ID",
    )
    config: Mapped[dict] = mapped_column(JSON, default=dict, comment="Agent 配置")
    success_rate: Mapped[Decimal] = mapped_column(Numeric(6, 2), default=0, comment="近 7 日成功率")
    call_count_7d: Mapped[int] = mapped_column(default=0, comment="近 7 日调用量")
    version: Mapped[str] = mapped_column(String(30), default="v0.1", comment="当前发布版本")
    created_by_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="创建人 ID",
    )

    model = relationship("LLMModel", lazy="selectin")
    creator = relationship("User", lazy="selectin")
    versions = relationship(
        "AgentVersion",
        back_populates="agent",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    @property
    def created_by(self) -> str | None:
        return self.creator.username if self.creator else None

    @property
    def model_name(self) -> str | None:
        return self.model.name if self.model else None


class AgentVersion(BaseModel):
    __tablename__ = "agent_versions"
    __table_args__ = (UniqueConstraint("agent_id", "version", name="uq_agent_versions_agent_version"),)

    agent_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("agents.id", ondelete="CASCADE"),
        index=True,
        comment="Agent ID",
    )
    version: Mapped[str] = mapped_column(String(30), comment="版本号")
    name: Mapped[str] = mapped_column(String(150), comment="名称快照")
    description: Mapped[str | None] = mapped_column(String(500), nullable=True, comment="描述快照")
    type: Mapped[str] = mapped_column(String(30), comment="类型快照")
    model_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True, comment="模型 ID 快照")
    config: Mapped[dict] = mapped_column(JSON, default=dict, comment="配置快照")
    changelog: Mapped[str | None] = mapped_column(String(500), nullable=True, comment="变更说明")
    is_current: Mapped[bool] = mapped_column(Boolean, default=False, index=True, comment="是否当前版本")
    published_by_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        comment="发布人 ID",
    )
    published_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, comment="发布时间")

    agent = relationship("Agent", back_populates="versions")
    publisher = relationship("User", lazy="selectin")

    @property
    def published_by(self) -> str | None:
        return self.publisher.username if self.publisher else None

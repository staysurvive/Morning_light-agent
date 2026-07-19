from datetime import datetime

from sqlalchemy import JSON, BigInteger, Boolean, DateTime, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.base_model import BaseModel


class Prompt(BaseModel):
    __tablename__ = "prompts"

    name: Mapped[str] = mapped_column(String(150), unique=True, index=True, comment="Prompt 名称")
    description: Mapped[str | None] = mapped_column(String(500), nullable=True, comment="Prompt 描述")
    category: Mapped[str] = mapped_column(String(50), default="general", index=True, comment="Prompt 分类")
    tags: Mapped[list[str]] = mapped_column(JSON, default=list, comment="标签")
    content: Mapped[str] = mapped_column(Text, comment="Prompt 内容")
    variables: Mapped[list[dict]] = mapped_column(JSON, default=list, comment="变量定义")
    version: Mapped[str] = mapped_column(String(30), default="v1.0", comment="当前发布版本")
    status: Mapped[str] = mapped_column(String(20), default="draft", index=True, comment="发布状态")
    created_by_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="创建人 ID",
    )

    creator = relationship("User", lazy="selectin", foreign_keys=[created_by_id])
    versions: Mapped[list["PromptVersion"]] = relationship(
        "PromptVersion",
        back_populates="prompt",
        cascade="all, delete-orphan",
        lazy="selectin",
        passive_deletes=True,
        order_by="PromptVersion.id.desc()",
    )

    @property
    def created_by(self) -> str | None:
        return self.creator.username if self.creator else None


class PromptVersion(BaseModel):
    __tablename__ = "prompt_versions"
    __table_args__ = (UniqueConstraint("prompt_id", "version", name="uq_prompt_versions_prompt_version"),)

    prompt_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("prompts.id", ondelete="CASCADE"),
        index=True,
        comment="Prompt ID",
    )
    version: Mapped[str] = mapped_column(String(30), comment="版本号")
    content: Mapped[str] = mapped_column(Text, comment="内容快照")
    variables: Mapped[list[dict]] = mapped_column(JSON, default=list, comment="变量快照")
    changelog: Mapped[str | None] = mapped_column(String(500), nullable=True, comment="变更说明")
    is_current: Mapped[bool] = mapped_column(Boolean, default=False, index=True, comment="是否当前版本")
    published_by_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        comment="发布人 ID",
    )
    published_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, comment="发布时间")

    prompt = relationship("Prompt", back_populates="versions")
    publisher = relationship("User", lazy="selectin", foreign_keys=[published_by_id])

    @property
    def published_by(self) -> str | None:
        return self.publisher.username if self.publisher else None

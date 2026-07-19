from typing import TYPE_CHECKING

from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.base_model import BaseModel

if TYPE_CHECKING:
    from src.modules.model.model import LLMModel


class ModelProvider(BaseModel):
    __tablename__ = "model_providers"

    name: Mapped[str] = mapped_column(String(100), unique=True, index=True, comment="供应商名称")
    type: Mapped[str] = mapped_column(String(30), index=True, comment="供应商类型")
    status: Mapped[str] = mapped_column(String(30), default="disconnected", index=True, comment="连接状态")
    endpoint: Mapped[str] = mapped_column(String(500), comment="API 端点")
    api_key_encrypted: Mapped[str | None] = mapped_column(Text, nullable=True, comment="加密后的 API Key")
    description: Mapped[str | None] = mapped_column(String(500), nullable=True, comment="供应商描述")

    models: Mapped[list["LLMModel"]] = relationship(
        "LLMModel",
        back_populates="provider",
        cascade="all, delete-orphan",
        lazy="selectin",
        passive_deletes=True,
    )

    @property
    def model_count(self) -> int:
        return len(self.models)

    @property
    def api_key_configured(self) -> bool:
        return bool(self.api_key_encrypted)

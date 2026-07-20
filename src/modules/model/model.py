from decimal import Decimal

from sqlalchemy import JSON, BigInteger, Boolean, ForeignKey, Numeric, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.base_model import BaseModel


class LLMModel(BaseModel):
    __tablename__ = "models"
    __table_args__ = (UniqueConstraint("provider_id", "model_id", name="uq_models_provider_model_id"),)

    name: Mapped[str] = mapped_column(String(100), index=True, comment="模型显示名称")
    model_id: Mapped[str] = mapped_column(String(150), index=True, comment="供应商模型标识")
    provider_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("model_providers.id", ondelete="CASCADE"),
        index=True,
        comment="供应商 ID",
    )
    capabilities: Mapped[list[str]] = mapped_column(JSON, default=list, comment="模型能力")
    context_length: Mapped[int] = mapped_column(default=4096, comment="上下文长度")
    status: Mapped[str] = mapped_column(String(30), default="available", index=True, comment="模型状态")
    input_price: Mapped[Decimal] = mapped_column(
        Numeric(18, 8), default=0, comment="每百万 Token 输入价格"
    )
    output_price: Mapped[Decimal] = mapped_column(
        Numeric(18, 8), default=0, comment="每百万 Token 输出价格"
    )
    currency: Mapped[str] = mapped_column(String(20), default="USD", comment="计价单位")
    is_default: Mapped[bool] = mapped_column(Boolean, default=False, index=True, comment="是否默认模型")
    description: Mapped[str | None] = mapped_column(Text, nullable=True, comment="模型描述")

    provider = relationship("ModelProvider", back_populates="models", lazy="selectin")

    @property
    def provider_name(self) -> str:
        return self.provider.name

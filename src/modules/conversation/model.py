from datetime import datetime
from decimal import Decimal

from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, JSON, Numeric, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.base_model import BaseModel


class Conversation(BaseModel):
    __tablename__ = "conversations"

    agent_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("agents.id", ondelete="SET NULL"), nullable=True, index=True, comment="Agent ID"
    )
    user_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True, comment="用户 ID"
    )
    model_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("models.id", ondelete="SET NULL"), nullable=True, index=True, comment="模型 ID"
    )
    agent_name_snapshot: Mapped[str] = mapped_column(String(150), comment="Agent 名称快照")
    user_name_snapshot: Mapped[str] = mapped_column(String(100), comment="用户名快照")
    model_name_snapshot: Mapped[str | None] = mapped_column(String(150), nullable=True, comment="模型名称快照")
    status: Mapped[str] = mapped_column(String(20), default="active", index=True, comment="会话状态")
    turn_count: Mapped[int] = mapped_column(default=0, comment="用户轮次数")
    input_tokens: Mapped[int] = mapped_column(default=0, comment="输入 Token")
    output_tokens: Mapped[int] = mapped_column(default=0, comment="输出 Token")
    cost: Mapped[Decimal] = mapped_column(Numeric(18, 8), default=0, comment="已记录成本")
    duration: Mapped[float] = mapped_column(default=0, comment="总时长（秒）")
    tags: Mapped[list[str]] = mapped_column(JSON, default=list, comment="会话标签")
    error_message: Mapped[str | None] = mapped_column(String(1000), nullable=True, comment="错误信息")
    started_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, index=True, comment="开始时间")
    ended_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, comment="结束时间")

    agent = relationship("Agent", lazy="selectin")
    user = relationship("User", lazy="selectin")
    model = relationship("LLMModel", lazy="selectin")
    turns = relationship(
        "ConversationTurn", back_populates="conversation", cascade="all, delete-orphan",
        passive_deletes=True, order_by="ConversationTurn.timestamp",
    )
    annotation = relationship(
        "ConversationAnnotation", back_populates="conversation", cascade="all, delete-orphan",
        passive_deletes=True, uselist=False, lazy="selectin",
    )

    @property
    def agent_name(self) -> str:
        return self.agent.name if self.agent else self.agent_name_snapshot

    @property
    def user_name(self) -> str:
        return self.user.username if self.user else self.user_name_snapshot

    @property
    def model_name(self) -> str | None:
        return self.model.name if self.model else self.model_name_snapshot

    @property
    def token_usage(self) -> int:
        return self.input_tokens + self.output_tokens

    @property
    def satisfaction(self) -> int | None:
        return self.annotation.rating if self.annotation else None


class ConversationTurn(BaseModel):
    __tablename__ = "conversation_turns"

    conversation_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("conversations.id", ondelete="CASCADE"), index=True, comment="会话 ID"
    )
    role: Mapped[str] = mapped_column(String(20), index=True, comment="消息角色")
    content: Mapped[str] = mapped_column(Text, comment="消息内容")
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, index=True, comment="消息时间")
    token_count: Mapped[int] = mapped_column(default=0, comment="消息 Token")
    tool_calls: Mapped[list[dict]] = mapped_column(JSON, default=list, comment="工具调用记录")

    conversation = relationship("Conversation", back_populates="turns")
    trace_steps = relationship(
        "TraceStep", back_populates="turn", cascade="all, delete-orphan",
        passive_deletes=True, order_by="TraceStep.start_time",
    )


class TraceStep(BaseModel):
    __tablename__ = "trace_steps"

    turn_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("conversation_turns.id", ondelete="CASCADE"), index=True, comment="轮次 ID"
    )
    type: Mapped[str] = mapped_column(String(20), index=True, comment="步骤类型")
    name: Mapped[str] = mapped_column(String(150), comment="步骤名称")
    input_data: Mapped[dict | list | str | int | float | bool | None] = mapped_column(JSON, nullable=True, comment="步骤输入")
    output_data: Mapped[dict | list | str | int | float | bool | None] = mapped_column(JSON, nullable=True, comment="步骤输出")
    start_time: Mapped[datetime] = mapped_column(DateTime, comment="开始时间")
    end_time: Mapped[datetime] = mapped_column(DateTime, comment="结束时间")
    duration: Mapped[int] = mapped_column(default=0, comment="耗时毫秒")
    status: Mapped[str] = mapped_column(String(20), comment="步骤状态")
    prompt_tokens: Mapped[int] = mapped_column(default=0, comment="输入 Token")
    completion_tokens: Mapped[int] = mapped_column(default=0, comment="输出 Token")
    total_tokens: Mapped[int] = mapped_column(default=0, comment="总 Token")
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict, comment="步骤元数据")

    turn = relationship("ConversationTurn", back_populates="trace_steps")


class ConversationAnnotation(BaseModel):
    __tablename__ = "conversation_annotations"
    __table_args__ = (UniqueConstraint("conversation_id", name="uq_conversation_annotations_conversation_id"),)

    conversation_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("conversations.id", ondelete="CASCADE"), index=True, comment="会话 ID"
    )
    rating: Mapped[int] = mapped_column(comment="评分 1-5")
    tags: Mapped[list[str]] = mapped_column(JSON, default=list, comment="问题标签")
    notes: Mapped[str | None] = mapped_column(Text, nullable=True, comment="标注说明")
    annotated_by_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, comment="标注人 ID"
    )
    annotated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, index=True, comment="标注时间")

    conversation = relationship("Conversation", back_populates="annotation")
    annotator = relationship("User", lazy="selectin")

    @property
    def annotated_by(self) -> str | None:
        return self.annotator.username if self.annotator else None

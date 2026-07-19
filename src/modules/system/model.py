from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.base_model import BaseModel


class ApiAccessKey(BaseModel):
    __tablename__ = "api_access_keys"

    name: Mapped[str] = mapped_column(String(150), unique=True, index=True, comment="API Key 名称")
    key_prefix: Mapped[str] = mapped_column(String(20), index=True, comment="Key 前缀")
    key_suffix: Mapped[str] = mapped_column(String(10), comment="Key 尾部")
    secret_hash: Mapped[str] = mapped_column(String(64), unique=True, comment="Key 哈希")
    permissions: Mapped[list[str]] = mapped_column(JSON, default=list, comment="权限码")
    status: Mapped[str] = mapped_column(String(20), default="active", index=True, comment="状态")
    rate_limit: Mapped[int] = mapped_column(default=100, comment="每分钟限额")
    usage_count: Mapped[int] = mapped_column(default=0, comment="使用次数")
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, comment="最后使用时间")
    expires_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, index=True, comment="过期时间")
    created_by_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True, comment="创建人 ID"
    )

    creator = relationship("User", lazy="selectin")

    @property
    def created_by(self) -> str | None:
        return self.creator.username if self.creator else None

    @property
    def effective_status(self) -> str:
        if self.status == "active" and self.expires_at and self.expires_at <= datetime.now():
            return "expired"
        return self.status

    @property
    def masked_key(self) -> str:
        return f"{self.key_prefix}{'*' * 20}{self.key_suffix}"


class AuditLog(BaseModel):
    __tablename__ = "audit_logs"

    user_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True, comment="用户 ID"
    )
    user_name: Mapped[str] = mapped_column(String(100), index=True, comment="用户名快照")
    action: Mapped[str] = mapped_column(String(50), index=True, comment="操作")
    resource: Mapped[str] = mapped_column(String(100), index=True, comment="资源类型")
    resource_name: Mapped[str] = mapped_column(String(500), comment="资源路径")
    details: Mapped[dict] = mapped_column(JSON, default=dict, comment="非敏感详情")
    ip_address: Mapped[str | None] = mapped_column(String(100), nullable=True, comment="来源 IP")
    user_agent: Mapped[str | None] = mapped_column(String(500), nullable=True, comment="User-Agent")
    status: Mapped[str] = mapped_column(String(20), index=True, comment="结果")
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, index=True, comment="发生时间")


class SystemAlert(BaseModel):
    __tablename__ = "system_alerts"

    type: Mapped[str] = mapped_column(String(20), index=True, comment="告警类型")
    title: Mapped[str] = mapped_column(String(200), comment="标题")
    message: Mapped[str] = mapped_column(String(1000), comment="消息")
    source: Mapped[str] = mapped_column(String(100), index=True, comment="来源")
    severity: Mapped[str] = mapped_column(String(20), index=True, comment="严重级别")
    status: Mapped[str] = mapped_column(String(20), default="active", index=True, comment="处理状态")
    count: Mapped[int] = mapped_column(default=1, comment="发生次数")
    first_occurred_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, comment="首次发生")
    last_occurred_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, index=True, comment="最近发生")
    acknowledged_by_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, comment="确认人 ID"
    )
    acknowledged_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, comment="确认时间")
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, comment="解决时间")

    acknowledger = relationship("User", lazy="selectin")

    @property
    def acknowledged_by(self) -> str | None:
        return self.acknowledger.username if self.acknowledger else None


class AlertRule(BaseModel):
    __tablename__ = "alert_rules"

    name: Mapped[str] = mapped_column(String(150), unique=True, index=True, comment="规则名称")
    description: Mapped[str | None] = mapped_column(String(500), nullable=True, comment="规则描述")
    condition: Mapped[dict] = mapped_column(JSON, comment="规则条件")
    notifications: Mapped[list[str]] = mapped_column(JSON, default=list, comment="通知渠道")
    status: Mapped[str] = mapped_column(String(20), default="enabled", index=True, comment="规则状态")
    created_by_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, comment="创建人 ID"
    )

    creator = relationship("User", lazy="selectin")

    @property
    def created_by(self) -> str | None:
        return self.creator.username if self.creator else None


class SystemSetting(BaseModel):
    __tablename__ = "system_settings"

    setting_key: Mapped[str] = mapped_column(String(50), unique=True, default="main", comment="设置标识")
    system_name: Mapped[str] = mapped_column(String(150), default="辰光 Agent", comment="系统名称")
    system_description: Mapped[str] = mapped_column(String(500), default="企业智能 Agent 管理平台", comment="系统描述")
    default_language: Mapped[str] = mapped_column(String(20), default="zh-CN", comment="默认语言")
    default_model: Mapped[str] = mapped_column(String(150), default="", comment="默认模型")
    default_temperature: Mapped[float] = mapped_column(default=0.7, comment="默认 Temperature")
    default_max_tokens: Mapped[int] = mapped_column(default=4096, comment="默认最大 Token")
    smtp_server: Mapped[str] = mapped_column(String(255), default="", comment="SMTP 服务器")
    smtp_port: Mapped[int] = mapped_column(default=587, comment="SMTP 端口")
    sender_email: Mapped[str] = mapped_column(String(255), default="", comment="发件人邮箱")
    updated_by_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, comment="更新人 ID"
    )

    updater = relationship("User", lazy="selectin")

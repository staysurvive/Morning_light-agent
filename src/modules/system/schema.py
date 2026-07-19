from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, model_validator


class ApiKeyCreate(BaseModel):
    name: str = Field(min_length=1, max_length=150)
    permissions: list[str] = Field(default_factory=list)
    rate_limit: int = Field(default=100, ge=1, le=1_000_000)
    expires_at: datetime | None = None


class ApiKeyUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=150)
    permissions: list[str] | None = None
    status: Literal["active", "disabled"] | None = None
    rate_limit: int | None = Field(default=None, ge=1, le=1_000_000)
    expires_at: datetime | None = None


class ApiKeyRead(BaseModel):
    id: int
    name: str
    key: str
    permissions: list[str]
    status: Literal["active", "disabled", "expired"]
    rateLimit: int
    usageCount: int
    lastUsedAt: datetime | None
    expiresAt: datetime | None
    createdBy: str | None
    createdAt: datetime


class ApiKeyCreated(ApiKeyRead):
    key: str = Field(description="仅本次响应返回完整密钥")


class AuditLogRead(BaseModel):
    id: int
    userId: str
    userName: str
    action: str
    resource: str
    resourceName: str
    details: dict
    ip: str
    userAgent: str
    status: Literal["success", "failed"]
    timestamp: datetime


class AlertCreate(BaseModel):
    type: Literal["error", "warning", "info"]
    title: str = Field(min_length=1, max_length=200)
    message: str = Field(min_length=1, max_length=1000)
    source: str = Field(min_length=1, max_length=100)
    severity: Literal["low", "medium", "high", "critical"]
    count: int = Field(default=1, ge=1)
    occurred_at: datetime | None = None


class AlertUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    message: str | None = Field(default=None, min_length=1, max_length=1000)
    severity: Literal["low", "medium", "high", "critical"] | None = None
    count: int | None = Field(default=None, ge=1)


class AlertRead(BaseModel):
    id: int
    type: str
    title: str
    message: str
    source: str
    severity: str
    status: str
    count: int
    firstOccurredAt: datetime
    lastOccurredAt: datetime
    acknowledgedBy: str | None
    acknowledgedAt: datetime | None
    resolvedAt: datetime | None


class RuleCondition(BaseModel):
    metric: str = Field(min_length=1, max_length=100)
    operator: Literal["gt", "lt", "eq", "gte", "lte"]
    threshold: float
    duration: int = Field(default=0, ge=0)


class AlertRuleCreate(BaseModel):
    name: str = Field(min_length=1, max_length=150)
    description: str | None = Field(default=None, max_length=500)
    condition: RuleCondition
    notifications: list[Literal["email", "webhook"]] = Field(default_factory=list)


class AlertRuleUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=150)
    description: str | None = Field(default=None, max_length=500)
    condition: RuleCondition | None = None
    notifications: list[Literal["email", "webhook"]] | None = None
    status: Literal["enabled", "disabled"] | None = None


class AlertRuleRead(BaseModel):
    id: int
    name: str
    description: str | None
    condition: dict
    notifications: list[str]
    status: str
    createdBy: str | None
    createdAt: datetime
    updatedAt: datetime


class SystemSettingsRead(BaseModel):
    systemName: str
    systemDescription: str
    defaultLanguage: str
    defaultModel: str
    defaultTemperature: float
    defaultMaxTokens: int
    smtpServer: str
    smtpPort: int
    senderEmail: str


class SystemSettingsUpdate(BaseModel):
    systemName: str | None = Field(default=None, min_length=1, max_length=150)
    systemDescription: str | None = Field(default=None, max_length=500)
    defaultLanguage: str | None = Field(default=None, min_length=1, max_length=20)
    defaultModel: str | None = Field(default=None, max_length=150)
    defaultTemperature: float | None = Field(default=None, ge=0, le=2)
    defaultMaxTokens: int | None = Field(default=None, ge=1, le=10_000_000)
    smtpServer: str | None = Field(default=None, max_length=255)
    smtpPort: int | None = Field(default=None, ge=1, le=65535)
    senderEmail: str | None = Field(default=None, max_length=255)

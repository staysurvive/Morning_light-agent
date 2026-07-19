from datetime import datetime
from typing import Literal

from pydantic import AnyHttpUrl, BaseModel, ConfigDict, Field, SecretStr


ProviderType = Literal["openai", "anthropic", "aliyun", "azure", "local", "custom"]
ProviderStatus = Literal["connected", "disconnected", "error"]


class ProviderCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    type: ProviderType
    endpoint: AnyHttpUrl
    api_key: SecretStr | None = None
    description: str | None = Field(default=None, max_length=500)


class ProviderUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    type: ProviderType | None = None
    endpoint: AnyHttpUrl | None = None
    api_key: SecretStr | None = None
    description: str | None = Field(default=None, max_length=500)


class ProviderRead(BaseModel):
    id: int
    name: str
    type: str
    status: ProviderStatus
    endpoint: str
    description: str | None
    model_count: int
    api_key_configured: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ProviderConnectionRead(BaseModel):
    success: bool
    message: str
    latency_ms: int
    status_code: int | None = None

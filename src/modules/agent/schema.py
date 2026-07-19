from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


AgentType = Literal["conversation", "tool", "analysis", "creative", "workflow"]
AgentStatus = Literal["active", "inactive", "error", "draft"]


class AgentCreate(BaseModel):
    name: str = Field(min_length=1, max_length=150)
    description: str | None = Field(default=None, max_length=500)
    type: AgentType
    model_id: int | None = Field(default=None, ge=1)
    config: dict[str, Any] = Field(default_factory=dict)


class AgentUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=150)
    description: str | None = Field(default=None, max_length=500)
    type: AgentType | None = None
    model_id: int | None = Field(default=None, ge=1)
    config: dict[str, Any] | None = None


class AgentRead(BaseModel):
    id: int
    name: str
    description: str | None
    type: AgentType
    status: AgentStatus
    model_id: int | None
    model_name: str | None
    config: dict[str, Any]
    success_rate: float
    call_count_7d: int
    version: str
    created_by: str | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AgentPublishRequest(BaseModel):
    changelog: str | None = Field(default=None, max_length=500)


class AgentRollbackRequest(BaseModel):
    version: str = Field(min_length=1, max_length=30)


class AgentVersionRead(BaseModel):
    id: int
    agent_id: int
    version: str
    config: dict[str, Any]
    changelog: str | None
    is_current: bool
    published_by: str | None
    published_at: datetime

    model_config = ConfigDict(from_attributes=True)

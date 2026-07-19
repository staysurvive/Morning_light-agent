from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


ConversationStatus = Literal["active", "completed", "failed"]


class ConversationCreate(BaseModel):
    agent_id: int = Field(ge=1)
    user_id: int | None = Field(default=None, ge=1)
    tags: list[str] = Field(default_factory=list)
    started_at: datetime | None = None


class ConversationUpdate(BaseModel):
    status: ConversationStatus | None = None
    cost: float | None = Field(default=None, ge=0)
    duration: float | None = Field(default=None, ge=0)
    tags: list[str] | None = None
    error_message: str | None = Field(default=None, max_length=1000)
    ended_at: datetime | None = None


class ConversationRead(BaseModel):
    id: int
    agent_id: int | None
    agent_name: str
    user_id: int | None
    user_name: str
    model_id: int | None
    model_name: str | None
    status: ConversationStatus
    turn_count: int
    token_usage: int
    input_tokens: int
    output_tokens: int
    cost: float
    duration: float
    satisfaction: int | None
    tags: list[str]
    error_message: str | None
    started_at: datetime
    ended_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TurnCreate(BaseModel):
    role: Literal["user", "assistant", "system"]
    content: str = Field(min_length=1)
    timestamp: datetime | None = None
    token_count: int = Field(default=0, ge=0)
    tool_calls: list[dict[str, Any]] = Field(default_factory=list)


class TurnRead(BaseModel):
    id: int
    conversation_id: int
    role: Literal["user", "assistant", "system"]
    content: str
    timestamp: datetime
    token_count: int
    tool_calls: list[dict[str, Any]]

    model_config = ConfigDict(from_attributes=True)


class TraceCreate(BaseModel):
    type: Literal["llm", "retrieval", "tool"]
    name: str = Field(min_length=1, max_length=150)
    input: Any = None
    output: Any = None
    start_time: datetime
    end_time: datetime
    duration: int | None = Field(default=None, ge=0)
    status: Literal["success", "failed"]
    prompt_tokens: int = Field(default=0, ge=0)
    completion_tokens: int = Field(default=0, ge=0)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_times(self):
        if self.end_time < self.start_time:
            raise ValueError("链路结束时间不能早于开始时间")
        return self


class TraceRead(BaseModel):
    id: int
    turn_id: int
    type: Literal["llm", "retrieval", "tool"]
    name: str
    input: Any = None
    output: Any = None
    start_time: datetime
    end_time: datetime
    duration: int
    status: Literal["success", "failed"]
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    metadata: dict[str, Any]


class AnnotationUpsert(BaseModel):
    rating: int = Field(ge=1, le=5)
    tags: list[str] = Field(default_factory=list)
    notes: str | None = None


class AnnotationRead(BaseModel):
    rating: int
    tags: list[str]
    notes: str | None
    annotated_by: str | None
    annotated_at: datetime

    model_config = ConfigDict(from_attributes=True)

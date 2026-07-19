from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class PromptVariableSchema(BaseModel):
    name: str = Field(min_length=1, max_length=100, pattern=r"^[A-Za-z_][A-Za-z0-9_]*$")
    type: Literal["string", "number", "boolean", "text"] = "string"
    description: str = Field(default="", max_length=300)
    default_value: str | None = None
    required: bool = False


class PromptCreate(BaseModel):
    name: str = Field(min_length=1, max_length=150)
    description: str | None = Field(default=None, max_length=500)
    category: str = Field(default="general", min_length=1, max_length=50)
    tags: list[str] = Field(default_factory=list)
    content: str = Field(min_length=1)
    variables: list[PromptVariableSchema] = Field(default_factory=list)


class PromptUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=150)
    description: str | None = Field(default=None, max_length=500)
    category: str | None = Field(default=None, min_length=1, max_length=50)
    tags: list[str] | None = None
    content: str | None = Field(default=None, min_length=1)
    variables: list[PromptVariableSchema] | None = None


class PromptRead(BaseModel):
    id: int
    name: str
    description: str | None
    category: str
    tags: list[str]
    content: str
    variables: list[PromptVariableSchema]
    version: str
    status: Literal["draft", "published"]
    created_by: str | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PromptPublishRequest(BaseModel):
    changelog: str | None = Field(default=None, max_length=500)


class PromptRollbackRequest(BaseModel):
    version: str = Field(min_length=1, max_length=30)


class PromptVersionRead(BaseModel):
    id: int
    prompt_id: int
    version: str
    content: str
    changelog: str | None
    is_current: bool
    published_by: str | None
    published_at: datetime | None

    model_config = ConfigDict(from_attributes=True)

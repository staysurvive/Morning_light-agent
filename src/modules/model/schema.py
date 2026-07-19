from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


ModelStatus = Literal["available", "unavailable", "rate_limited"]


class ModelCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    model_id: str = Field(min_length=1, max_length=150)
    provider_id: int
    capabilities: list[str] = Field(default_factory=list)
    context_length: int = Field(default=4096, ge=1, le=10_000_000)
    input_price: float = Field(default=0, ge=0)
    output_price: float = Field(default=0, ge=0)
    currency: str = Field(default="USD", min_length=1, max_length=20)
    is_default: bool = False
    description: str | None = None


class ModelUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    capabilities: list[str] | None = None
    context_length: int | None = Field(default=None, ge=1, le=10_000_000)
    status: ModelStatus | None = None
    input_price: float | None = Field(default=None, ge=0)
    output_price: float | None = Field(default=None, ge=0)
    currency: str | None = Field(default=None, min_length=1, max_length=20)
    is_default: bool | None = None
    description: str | None = None


class ModelRead(BaseModel):
    id: int
    name: str
    model_id: str
    provider_id: int
    provider_name: str
    capabilities: list[str]
    context_length: int
    status: ModelStatus
    input_price: float
    output_price: float
    currency: str
    is_default: bool
    description: str | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

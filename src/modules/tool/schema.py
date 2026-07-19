from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


ToolType = Literal["builtin", "http_api", "custom_function"]
ToolStatus = Literal["enabled", "disabled", "error"]


class FunctionDefinition(BaseModel):
    name: str = Field(min_length=1, max_length=100, pattern=r"^[A-Za-z_][A-Za-z0-9_]*$")
    description: str = Field(default="", max_length=500)
    parameters: dict[str, Any] = Field(default_factory=lambda: {"type": "object", "properties": {}, "required": []})

    @model_validator(mode="after")
    def validate_parameters(self):
        if self.parameters.get("type") != "object":
            raise ValueError("函数参数定义的 type 必须为 object")
        properties = self.parameters.get("properties", {})
        required = self.parameters.get("required", [])
        if not isinstance(properties, dict) or not isinstance(required, list):
            raise ValueError("函数参数定义格式错误")
        if any(name not in properties for name in required):
            raise ValueError("必填参数必须在 properties 中定义")
        return self


class ToolCreate(BaseModel):
    name: str = Field(min_length=1, max_length=150)
    description: str | None = Field(default=None, max_length=500)
    type: ToolType
    config: dict[str, Any] = Field(default_factory=dict)
    function_definition: FunctionDefinition | None = None


class ToolUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=150)
    description: str | None = Field(default=None, max_length=500)
    type: ToolType | None = None
    config: dict[str, Any] | None = None
    function_definition: FunctionDefinition | None = None


class ToolRead(BaseModel):
    id: int
    name: str
    description: str | None
    type: ToolType
    status: ToolStatus
    config: dict[str, Any]
    function_definition: dict[str, Any] | None
    call_count_7d: int
    success_rate: float
    avg_latency: float
    created_by: str | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ToolTestRequest(BaseModel):
    input: dict[str, Any] = Field(default_factory=dict)


class ToolTestResult(BaseModel):
    success: bool
    output: Any = None
    error: str | None = None
    latency_ms: int = 0

    @field_validator("latency_ms")
    @classmethod
    def latency_is_non_negative(cls, value: int) -> int:
        return max(0, value)

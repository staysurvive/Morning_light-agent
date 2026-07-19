import json
from time import perf_counter
from urllib.parse import urlparse

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.crypto import decrypt_secret, encrypt_secret
from src.core.exceptions import BizException
from src.core.network import assert_public_http_target
from src.modules.tool.model import Tool, ToolExecution
from src.modules.tool.repository import ToolExecutionRepository, ToolRepository
from src.modules.tool.schema import ToolCreate, ToolTestResult, ToolUpdate
from src.modules.user.model import User


SENSITIVE_HEADER_NAMES = {"authorization", "proxy-authorization", "x-api-key", "api-key", "cookie", "set-cookie"}


def _encrypt_config(config: dict) -> str:
    return encrypt_secret(json.dumps(config, ensure_ascii=False, separators=(",", ":")))


def _decrypt_config(tool: Tool) -> dict:
    value = decrypt_secret(tool.config_encrypted)
    if not value:
        return {}
    try:
        result = json.loads(value)
    except json.JSONDecodeError as exc:
        raise BizException(code=500, message="工具配置无法解密") from exc
    return result if isinstance(result, dict) else {}


def _redact_config(config: dict) -> dict:
    result = json.loads(json.dumps(config))
    headers = result.get("headers")
    if isinstance(headers, dict):
        for key in list(headers):
            if key.lower() in SENSITIVE_HEADER_NAMES or any(part in key.lower() for part in ("token", "secret")):
                headers[key] = "***configured***"
    return result


def _restore_redacted_headers(config: dict, previous: dict) -> dict:
    result = json.loads(json.dumps(config))
    headers = result.get("headers")
    previous_headers = previous.get("headers", {})
    if isinstance(headers, dict) and isinstance(previous_headers, dict):
        for key, value in headers.items():
            if value == "***configured***" and key in previous_headers:
                headers[key] = previous_headers[key]
    return result


def _validate_http_config(config: dict) -> None:
    method = str(config.get("method", "GET")).upper()
    if method not in {"GET", "POST", "PUT", "PATCH", "DELETE"}:
        raise BizException(code=400, message="HTTP 工具仅支持 GET、POST、PUT、PATCH、DELETE")
    url = str(config.get("url", "")).strip()
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise BizException(code=400, message="HTTP 工具必须配置有效的 HTTP(S) URL")
    timeout = config.get("timeout", config.get("timeout_ms", 10000))
    if not isinstance(timeout, (int, float)) or timeout < 100 or timeout > 15000:
        raise BizException(code=400, message="HTTP 工具超时必须在 100 到 15000 毫秒之间")
    headers = config.get("headers", {})
    if not isinstance(headers, dict) or any(not isinstance(k, str) or not isinstance(v, str) for k, v in headers.items()):
        raise BizException(code=400, message="HTTP 请求头必须是字符串键值对象")


class ToolService:
    def __init__(self, db: AsyncSession):
        self.repo = ToolRepository(db)
        self.execution_repo = ToolExecutionRepository(db)

    def serialize(self, tool: Tool) -> dict:
        return {
            "id": tool.id,
            "name": tool.name,
            "description": tool.description,
            "type": tool.type,
            "status": tool.status,
            "config": _redact_config(_decrypt_config(tool)),
            "function_definition": tool.function_definition,
            "call_count_7d": tool.call_count_7d,
            "success_rate": float(tool.success_rate),
            "avg_latency": float(tool.avg_latency),
            "created_by": tool.created_by,
            "created_at": tool.created_at,
            "updated_at": tool.updated_at,
        }

    def _validate_config(self, tool_type: str, config: dict) -> None:
        if tool_type == "http_api":
            _validate_http_config(config)

    async def create_tool(self, data: ToolCreate, current_user: User) -> Tool:
        name = data.name.strip()
        if await self.repo.get_by_name(name):
            raise BizException(code=400, message="工具名称已存在")
        self._validate_config(data.type, data.config)
        return await self.repo.create(Tool(
            name=name,
            description=data.description.strip() if data.description else None,
            type=data.type,
            status="disabled",
            config_encrypted=_encrypt_config(data.config),
            function_definition=data.function_definition.model_dump() if data.function_definition else None,
            creator=current_user,
        ))

    async def get_tool(self, tool_id: int, refresh_metrics: bool = True) -> Tool:
        tool = await self.repo.get_by_id(tool_id)
        if not tool:
            raise BizException(code=404, message="工具不存在")
        if refresh_metrics:
            await self.repo.refresh_metrics(tool)
        return tool

    async def search_page(self, offset: int, limit: int, keyword: str | None):
        return await self.repo.search_page(offset, limit, keyword)

    async def update_tool(self, tool_id: int, data: ToolUpdate) -> Tool:
        tool = await self.get_tool(tool_id, refresh_metrics=False)
        values = data.model_dump(exclude_unset=True)
        if data.name is not None:
            name = data.name.strip()
            duplicate = await self.repo.get_by_name(name)
            if duplicate and duplicate.id != tool.id:
                raise BizException(code=400, message="工具名称已存在")
            tool.name = name
        if "description" in values:
            tool.description = data.description.strip() if data.description else None
        new_type = data.type or tool.type
        old_config = _decrypt_config(tool)
        new_config = data.config if data.config is not None else old_config
        if data.config is not None:
            new_config = _restore_redacted_headers(new_config, old_config)
        self._validate_config(new_type, new_config)
        if data.type is not None:
            tool.type = data.type
        if data.config is not None:
            tool.config_encrypted = _encrypt_config(new_config)
        if "function_definition" in values:
            tool.function_definition = data.function_definition.model_dump() if data.function_definition else None
        if values:
            tool.status = "disabled"
        return await self.repo.update(tool)

    async def delete_tool(self, tool_id: int) -> None:
        if not await self.repo.delete_by_id(tool_id):
            raise BizException(code=404, message="工具不存在")

    async def set_enabled(self, tool_id: int, enabled: bool) -> Tool:
        tool = await self.get_tool(tool_id, refresh_metrics=False)
        if enabled:
            self._validate_config(tool.type, _decrypt_config(tool))
        tool.status = "enabled" if enabled else "disabled"
        return await self.repo.update(tool)

    def _validate_input(self, tool: Tool, input_data: dict) -> None:
        definition = tool.function_definition or {}
        parameters = definition.get("parameters", {}) if isinstance(definition, dict) else {}
        required = parameters.get("required", []) if isinstance(parameters, dict) else []
        missing = [name for name in required if name not in input_data]
        if missing:
            raise BizException(code=400, message=f"缺少必填参数：{', '.join(missing)}")

    async def test_tool(self, tool_id: int, input_data: dict) -> ToolTestResult:
        tool = await self.get_tool(tool_id, refresh_metrics=False)
        self._validate_input(tool, input_data)
        started = perf_counter()
        if tool.type != "http_api":
            result = ToolTestResult(
                success=False,
                error="当前后端没有内置工具或自定义函数执行沙箱，仅支持配置管理",
                latency_ms=0,
            )
            await self._record_execution(tool, result)
            return result

        config = _decrypt_config(tool)
        _validate_http_config(config)
        url = str(config["url"])
        await assert_public_http_target(url)
        method = str(config.get("method", "GET")).upper()
        timeout_ms = int(config.get("timeout", config.get("timeout_ms", 10000)))
        try:
            async with httpx.AsyncClient(
                timeout=timeout_ms / 1000,
                follow_redirects=False,
                trust_env=False,
            ) as client:
                request_kwargs = {"headers": config.get("headers", {})}
                if method == "GET":
                    request_kwargs["params"] = input_data
                else:
                    request_kwargs["json"] = input_data
                response = await client.request(method, url, **request_kwargs)
            latency_ms = round((perf_counter() - started) * 1000)
            content_length = len(response.content)
            if content_length > 1024 * 1024:
                result = ToolTestResult(success=False, error="HTTP 工具响应超过 1MB 限制", latency_ms=latency_ms)
            else:
                try:
                    output = response.json()
                except ValueError:
                    output = response.text
                success = 200 <= response.status_code < 300
                result = ToolTestResult(
                    success=success,
                    output={"status_code": response.status_code, "body": output},
                    error=None if success else f"HTTP {response.status_code}",
                    latency_ms=latency_ms,
                )
        except httpx.HTTPError as exc:
            result = ToolTestResult(
                success=False,
                error=f"HTTP 工具请求失败：{exc}",
                latency_ms=round((perf_counter() - started) * 1000),
            )
        await self._record_execution(tool, result)
        return result

    async def _record_execution(self, tool: Tool, result: ToolTestResult) -> None:
        await self.execution_repo.create(ToolExecution(
            tool_id=tool.id,
            success=result.success,
            latency_ms=result.latency_ms,
            is_test=True,
            error=result.error[:1000] if result.error else None,
        ))
        await self.repo.refresh_metrics(tool)

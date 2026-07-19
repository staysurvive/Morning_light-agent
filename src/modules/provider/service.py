from time import perf_counter

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.crypto import decrypt_secret, encrypt_secret
from src.core.exceptions import BizException
from src.core.network import assert_public_http_target
from src.modules.provider.model import ModelProvider
from src.modules.provider.repository import ProviderRepository
from src.modules.provider.schema import ProviderConnectionRead, ProviderCreate, ProviderUpdate


class ProviderService:
    def __init__(self, db: AsyncSession):
        self.repo = ProviderRepository(db)

    async def create_provider(self, data: ProviderCreate) -> ModelProvider:
        name = data.name.strip()
        if await self.repo.get_by_name(name):
            raise BizException(code=400, message="供应商名称已存在")
        api_key = data.api_key.get_secret_value().strip() if data.api_key else ""
        provider = ModelProvider(
            name=name,
            type=data.type,
            status="disconnected",
            endpoint=str(data.endpoint).rstrip("/"),
            api_key_encrypted=encrypt_secret(api_key) if api_key else None,
            description=data.description.strip() if data.description else None,
        )
        return await self.repo.create(provider)

    async def get_provider(self, provider_id: int) -> ModelProvider:
        provider = await self.repo.get_by_id(provider_id)
        if not provider:
            raise BizException(code=404, message="模型供应商不存在")
        return provider

    async def search_page(
        self,
        offset: int,
        limit: int,
        keyword: str | None,
    ) -> tuple[list[ModelProvider], int]:
        return await self.repo.search_page(offset, limit, keyword)

    async def update_provider(self, provider_id: int, data: ProviderUpdate) -> ModelProvider:
        provider = await self.get_provider(provider_id)
        values = data.model_dump(exclude_unset=True)
        if "name" in values and data.name is not None:
            name = data.name.strip()
            duplicate = await self.repo.get_by_name(name)
            if duplicate and duplicate.id != provider.id:
                raise BizException(code=400, message="供应商名称已存在")
            provider.name = name
        if data.type is not None:
            provider.type = data.type
        if data.endpoint is not None:
            provider.endpoint = str(data.endpoint).rstrip("/")
            provider.status = "disconnected"
        if "api_key" in values and data.api_key:
            api_key = data.api_key.get_secret_value().strip()
            if api_key:
                provider.api_key_encrypted = encrypt_secret(api_key)
                provider.status = "disconnected"
        if "description" in values:
            provider.description = data.description.strip() if data.description else None
        return await self.repo.update(provider)

    async def delete_provider(self, provider_id: int) -> None:
        if not await self.repo.delete_by_id(provider_id):
            raise BizException(code=404, message="模型供应商不存在")

    async def test_connection(self, provider_id: int) -> ProviderConnectionRead:
        provider = await self.get_provider(provider_id)
        api_key = decrypt_secret(provider.api_key_encrypted)
        headers = {"Authorization": f"Bearer {api_key}"} if api_key else {}
        started = perf_counter()
        try:
            await assert_public_http_target(provider.endpoint)
            async with httpx.AsyncClient(timeout=5.0, follow_redirects=False, trust_env=False) as client:
                response = await client.get(provider.endpoint, headers=headers)
            latency_ms = round((perf_counter() - started) * 1000)
            success = response.status_code < 500 and response.status_code not in {401, 403}
            provider.status = "connected" if success else "error"
            await self.repo.update(provider)
            message = "连接成功" if success else f"连接失败，HTTP {response.status_code}"
            return ProviderConnectionRead(
                success=success,
                message=message,
                latency_ms=latency_ms,
                status_code=response.status_code,
            )
        except (httpx.HTTPError, ValueError) as exc:
            provider.status = "error"
            await self.repo.update(provider)
            return ProviderConnectionRead(
                success=False,
                message=f"连接失败：{exc}",
                latency_ms=round((perf_counter() - started) * 1000),
            )

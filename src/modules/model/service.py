from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from src.core.exceptions import BizException
from src.modules.model.model import LLMModel
from src.modules.model.repository import ModelRepository
from src.modules.model.schema import ModelCreate, ModelUpdate
from src.modules.provider.repository import ProviderRepository


class ModelService:
    def __init__(self, db: AsyncSession):
        self.repo = ModelRepository(db)
        self.provider_repo = ProviderRepository(db)

    async def create_model(self, data: ModelCreate) -> LLMModel:
        provider = await self.provider_repo.get_by_id(data.provider_id)
        if not provider:
            raise BizException(code=400, message="模型供应商不存在")
        model_id = data.model_id.strip()
        if await self.repo.get_by_provider_model_id(data.provider_id, model_id):
            raise BizException(code=400, message="该供应商下的 Model ID 已存在")
        if data.is_default:
            await self.repo.clear_default()
        model = LLMModel(
            name=data.name.strip(),
            model_id=model_id,
            provider=provider,
            capabilities=list(dict.fromkeys(data.capabilities)),
            context_length=data.context_length,
            status="available",
            input_price=Decimal(str(data.input_price)),
            output_price=Decimal(str(data.output_price)),
            currency=data.currency.strip(),
            is_default=data.is_default,
            description=data.description.strip() if data.description else None,
        )
        return await self.repo.create(model)

    async def get_model(self, model_id: int) -> LLMModel:
        model = await self.repo.get_by_id(model_id)
        if not model:
            raise BizException(code=404, message="模型不存在")
        return model

    async def search_page(self, offset: int, limit: int, keyword: str | None, provider_id: int | None):
        return await self.repo.search_page(offset, limit, keyword, provider_id)

    async def update_model(self, model_id: int, data: ModelUpdate) -> LLMModel:
        model = await self.get_model(model_id)
        values = data.model_dump(exclude_unset=True)
        if data.name is not None:
            model.name = data.name.strip()
        if data.capabilities is not None:
            model.capabilities = list(dict.fromkeys(data.capabilities))
        if data.context_length is not None:
            model.context_length = data.context_length
        if data.status is not None:
            model.status = data.status
        if data.input_price is not None:
            model.input_price = Decimal(str(data.input_price))
        if data.output_price is not None:
            model.output_price = Decimal(str(data.output_price))
        if data.currency is not None:
            model.currency = data.currency.strip()
        if data.is_default is not None:
            if data.is_default:
                await self.repo.clear_default(exclude_id=model.id)
            model.is_default = data.is_default
        if "description" in values:
            model.description = data.description.strip() if data.description else None
        return await self.repo.update(model)

    async def delete_model(self, model_id: int) -> None:
        if not await self.repo.delete_by_id(model_id):
            raise BizException(code=404, message="模型不存在")

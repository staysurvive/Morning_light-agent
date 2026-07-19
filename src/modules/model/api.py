from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.base_schema import PageResult, ResponseSchema
from src.core.deps import PageParams, require_permission
from src.core.permissions import MODEL_CREATE, MODEL_DELETE, MODEL_READ, MODEL_UPDATE
from src.infra.database import get_db
from src.modules.model.schema import ModelCreate, ModelRead, ModelUpdate
from src.modules.model.service import ModelService

router = APIRouter(prefix="/models", tags=["Model"])


def get_model_service(db: AsyncSession = Depends(get_db, scope="function")) -> ModelService:
    return ModelService(db)


@router.get("", response_model=ResponseSchema[PageResult[ModelRead]], dependencies=[Depends(require_permission(MODEL_READ))])
async def list_models(
    params: PageParams = Depends(),
    provider_id: int | None = Query(default=None, ge=1),
    service: ModelService = Depends(get_model_service),
):
    items, total = await service.search_page(params.offset, params.page_size, params.keyword, provider_id)
    return ResponseSchema(data=PageResult(
        items=[ModelRead.model_validate(item) for item in items],
        total=total,
        page=params.page,
        page_size=params.page_size,
    ))


@router.post("", response_model=ResponseSchema[ModelRead], dependencies=[Depends(require_permission(MODEL_CREATE))])
async def create_model(data: ModelCreate, service: ModelService = Depends(get_model_service)):
    return ResponseSchema(data=ModelRead.model_validate(await service.create_model(data)))


@router.get("/{model_id}", response_model=ResponseSchema[ModelRead], dependencies=[Depends(require_permission(MODEL_READ))])
async def get_model(model_id: int, service: ModelService = Depends(get_model_service)):
    return ResponseSchema(data=ModelRead.model_validate(await service.get_model(model_id)))


@router.put("/{model_id}", response_model=ResponseSchema[ModelRead], dependencies=[Depends(require_permission(MODEL_UPDATE))])
async def update_model(model_id: int, data: ModelUpdate, service: ModelService = Depends(get_model_service)):
    return ResponseSchema(data=ModelRead.model_validate(await service.update_model(model_id, data)))


@router.delete("/{model_id}", response_model=ResponseSchema[None], dependencies=[Depends(require_permission(MODEL_DELETE))])
async def delete_model(model_id: int, service: ModelService = Depends(get_model_service)):
    await service.delete_model(model_id)
    return ResponseSchema(data=None)

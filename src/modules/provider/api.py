from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.base_schema import PageResult, ResponseSchema
from src.core.deps import PageParams, require_permission
from src.core.permissions import (
    PROVIDER_CREATE,
    PROVIDER_DELETE,
    PROVIDER_READ,
    PROVIDER_TEST,
    PROVIDER_UPDATE,
)
from src.infra.database import get_db
from src.modules.provider.schema import (
    ProviderConnectionRead,
    ProviderCreate,
    ProviderRead,
    ProviderUpdate,
)
from src.modules.provider.service import ProviderService

router = APIRouter(prefix="/providers", tags=["Model Provider"])


def get_provider_service(db: AsyncSession = Depends(get_db, scope="function")) -> ProviderService:
    return ProviderService(db)


@router.get("", response_model=ResponseSchema[PageResult[ProviderRead]], dependencies=[Depends(require_permission(PROVIDER_READ))])
async def list_providers(params: PageParams = Depends(), service: ProviderService = Depends(get_provider_service)):
    items, total = await service.search_page(params.offset, params.page_size, params.keyword)
    return ResponseSchema(data=PageResult(
        items=[ProviderRead.model_validate(item) for item in items],
        total=total,
        page=params.page,
        page_size=params.page_size,
    ))


@router.post("", response_model=ResponseSchema[ProviderRead], dependencies=[Depends(require_permission(PROVIDER_CREATE))])
async def create_provider(data: ProviderCreate, service: ProviderService = Depends(get_provider_service)):
    return ResponseSchema(data=ProviderRead.model_validate(await service.create_provider(data)))


@router.get("/{provider_id}", response_model=ResponseSchema[ProviderRead], dependencies=[Depends(require_permission(PROVIDER_READ))])
async def get_provider(provider_id: int, service: ProviderService = Depends(get_provider_service)):
    return ResponseSchema(data=ProviderRead.model_validate(await service.get_provider(provider_id)))


@router.put("/{provider_id}", response_model=ResponseSchema[ProviderRead], dependencies=[Depends(require_permission(PROVIDER_UPDATE))])
async def update_provider(provider_id: int, data: ProviderUpdate, service: ProviderService = Depends(get_provider_service)):
    return ResponseSchema(data=ProviderRead.model_validate(await service.update_provider(provider_id, data)))


@router.delete("/{provider_id}", response_model=ResponseSchema[None], dependencies=[Depends(require_permission(PROVIDER_DELETE))])
async def delete_provider(provider_id: int, service: ProviderService = Depends(get_provider_service)):
    await service.delete_provider(provider_id)
    return ResponseSchema(data=None)


@router.post("/{provider_id}/test", response_model=ResponseSchema[ProviderConnectionRead], dependencies=[Depends(require_permission(PROVIDER_TEST))])
async def test_provider_connection(provider_id: int, service: ProviderService = Depends(get_provider_service)):
    return ResponseSchema(data=await service.test_connection(provider_id))

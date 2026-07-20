from fastapi import APIRouter, BackgroundTasks, Depends, File, Query, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.base_schema import PageResult, ResponseSchema
from src.core.deps import PageParams, require_permission
from src.core.permissions import (
    KNOWLEDGE_CREATE,
    KNOWLEDGE_DELETE,
    KNOWLEDGE_DOCUMENT_MANAGE,
    KNOWLEDGE_READ,
    KNOWLEDGE_RETRIEVE,
    KNOWLEDGE_SEGMENT_UPDATE,
    KNOWLEDGE_UPDATE,
)
from src.infra.database import get_db
from src.modules.knowledge.schema import (
    DocumentRead,
    KnowledgeBaseConfigUpdate,
    KnowledgeBaseCreate,
    KnowledgeBaseRead,
    KnowledgeBaseUpdate,
    RetrievalTestRequest,
    RetrievalTestResult,
    SegmentRead,
    SegmentUpdate,
)
from src.modules.knowledge.service import KnowledgeService
from src.modules.knowledge.tasks import process_document
from src.modules.user.model import User

router = APIRouter(prefix="/knowledge-bases", tags=["Knowledge"])


def get_knowledge_service(db: AsyncSession = Depends(get_db, scope="function")) -> KnowledgeService:
    return KnowledgeService(db)


@router.get("", response_model=ResponseSchema[PageResult[KnowledgeBaseRead]], dependencies=[Depends(require_permission(KNOWLEDGE_READ))])
async def list_knowledge_bases(params: PageParams = Depends(), service: KnowledgeService = Depends(get_knowledge_service)):
    items, total = await service.search_page(params.offset, params.page_size, params.keyword)
    return ResponseSchema(data=PageResult(
        items=[KnowledgeBaseRead.model_validate(item) for item in items],
        total=total,
        page=params.page,
        page_size=params.page_size,
    ))


@router.post("", response_model=ResponseSchema[KnowledgeBaseRead])
async def create_knowledge_base(
    data: KnowledgeBaseCreate,
    current_user: User = Depends(require_permission(KNOWLEDGE_CREATE)),
    service: KnowledgeService = Depends(get_knowledge_service),
):
    return ResponseSchema(data=KnowledgeBaseRead.model_validate(await service.create_base(data, current_user)))


@router.get("/{knowledge_base_id}", response_model=ResponseSchema[KnowledgeBaseRead], dependencies=[Depends(require_permission(KNOWLEDGE_READ))])
async def get_knowledge_base(knowledge_base_id: int, service: KnowledgeService = Depends(get_knowledge_service)):
    return ResponseSchema(data=KnowledgeBaseRead.model_validate(await service.get_base(knowledge_base_id)))


@router.put("/{knowledge_base_id}", response_model=ResponseSchema[KnowledgeBaseRead], dependencies=[Depends(require_permission(KNOWLEDGE_UPDATE))])
async def update_knowledge_base(knowledge_base_id: int, data: KnowledgeBaseUpdate, service: KnowledgeService = Depends(get_knowledge_service)):
    return ResponseSchema(data=KnowledgeBaseRead.model_validate(await service.update_base(knowledge_base_id, data)))


@router.put("/{knowledge_base_id}/config", response_model=ResponseSchema[KnowledgeBaseRead], dependencies=[Depends(require_permission(KNOWLEDGE_UPDATE))])
async def update_knowledge_base_config(knowledge_base_id: int, data: KnowledgeBaseConfigUpdate, service: KnowledgeService = Depends(get_knowledge_service)):
    return ResponseSchema(data=KnowledgeBaseRead.model_validate(await service.update_config(knowledge_base_id, data)))


@router.delete("/{knowledge_base_id}", response_model=ResponseSchema[None], dependencies=[Depends(require_permission(KNOWLEDGE_DELETE))])
async def delete_knowledge_base(knowledge_base_id: int, service: KnowledgeService = Depends(get_knowledge_service)):
    await service.delete_base(knowledge_base_id)
    return ResponseSchema(data=None)


@router.get("/{knowledge_base_id}/documents", response_model=ResponseSchema[PageResult[DocumentRead]], dependencies=[Depends(require_permission(KNOWLEDGE_READ))])
async def list_documents(knowledge_base_id: int, params: PageParams = Depends(), service: KnowledgeService = Depends(get_knowledge_service)):
    items, total = await service.list_documents(knowledge_base_id, params.offset, params.page_size, params.keyword)
    return ResponseSchema(data=PageResult(
        items=[DocumentRead.model_validate(item) for item in items], total=total,
        page=params.page, page_size=params.page_size,
    ))


@router.post("/{knowledge_base_id}/documents", response_model=ResponseSchema[DocumentRead])
async def upload_document(
    knowledge_base_id: int,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    current_user: User = Depends(require_permission(KNOWLEDGE_DOCUMENT_MANAGE)),
    service: KnowledgeService = Depends(get_knowledge_service),
):
    document = await service.upload_document(knowledge_base_id, file, current_user)
    background_tasks.add_task(process_document, document.id)
    return ResponseSchema(data=DocumentRead.model_validate(document))


@router.delete("/{knowledge_base_id}/documents/{document_id}", response_model=ResponseSchema[None], dependencies=[Depends(require_permission(KNOWLEDGE_DOCUMENT_MANAGE))])
async def delete_document(knowledge_base_id: int, document_id: int, service: KnowledgeService = Depends(get_knowledge_service)):
    await service.delete_document(knowledge_base_id, document_id)
    return ResponseSchema(data=None)


@router.post("/{knowledge_base_id}/documents/{document_id}/retry", response_model=ResponseSchema[DocumentRead], dependencies=[Depends(require_permission(KNOWLEDGE_DOCUMENT_MANAGE))])
async def retry_document(
    knowledge_base_id: int,
    document_id: int,
    background_tasks: BackgroundTasks,
    service: KnowledgeService = Depends(get_knowledge_service),
):
    document = await service.retry_document(knowledge_base_id, document_id)
    background_tasks.add_task(process_document, document.id)
    return ResponseSchema(data=DocumentRead.model_validate(document))


@router.get("/{knowledge_base_id}/segments", response_model=ResponseSchema[PageResult[SegmentRead]], dependencies=[Depends(require_permission(KNOWLEDGE_READ))])
async def list_segments(
    knowledge_base_id: int,
    params: PageParams = Depends(),
    document_id: int | None = Query(default=None, ge=1),
    service: KnowledgeService = Depends(get_knowledge_service),
):
    items, total = await service.list_segments(
        knowledge_base_id, params.offset, params.page_size, document_id, params.keyword
    )
    return ResponseSchema(data=PageResult(
        items=[SegmentRead.model_validate(item) for item in items], total=total,
        page=params.page, page_size=params.page_size,
    ))


@router.get("/{knowledge_base_id}/documents/{document_id}/segments", response_model=ResponseSchema[PageResult[SegmentRead]], dependencies=[Depends(require_permission(KNOWLEDGE_READ))])
async def list_document_segments(
    knowledge_base_id: int,
    document_id: int,
    params: PageParams = Depends(),
    service: KnowledgeService = Depends(get_knowledge_service),
):
    items, total = await service.list_segments(
        knowledge_base_id, params.offset, params.page_size, document_id, params.keyword
    )
    return ResponseSchema(data=PageResult(
        items=[SegmentRead.model_validate(item) for item in items], total=total,
        page=params.page, page_size=params.page_size,
    ))


@router.put("/{knowledge_base_id}/segments/{segment_id}", response_model=ResponseSchema[SegmentRead], dependencies=[Depends(require_permission(KNOWLEDGE_SEGMENT_UPDATE))])
async def update_segment(knowledge_base_id: int, segment_id: int, data: SegmentUpdate, service: KnowledgeService = Depends(get_knowledge_service)):
    return ResponseSchema(data=SegmentRead.model_validate(
        await service.update_segment(knowledge_base_id, segment_id, data)
    ))


@router.post("/{knowledge_base_id}/retrieval-test", response_model=ResponseSchema[list[RetrievalTestResult]], dependencies=[Depends(require_permission(KNOWLEDGE_RETRIEVE))])
async def retrieval_test(knowledge_base_id: int, data: RetrievalTestRequest, service: KnowledgeService = Depends(get_knowledge_service)):
    results = await service.retrieval_test(knowledge_base_id, data.query, data.top_k, data.similarity_threshold)
    return ResponseSchema(data=[RetrievalTestResult.model_validate(item) for item in results])

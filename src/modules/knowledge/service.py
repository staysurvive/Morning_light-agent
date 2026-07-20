import asyncio
import re
import uuid
from pathlib import Path

from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import get_settings
from src.core.exceptions import BizException
from src.infra.minio_client import delete_object, upload_file
from src.modules.knowledge.model import Document, KnowledgeBase, Segment
from src.modules.knowledge.parser import SUPPORTED_DOCUMENT_TYPES, estimate_tokens, text_terms
from src.modules.knowledge.repository import DocumentRepository, KnowledgeBaseRepository, SegmentRepository
from src.modules.knowledge.schema import KnowledgeBaseConfigUpdate, KnowledgeBaseCreate, KnowledgeBaseUpdate, SegmentUpdate
from src.modules.knowledge.tasks import process_document_in_session, refresh_knowledge_base_counts
from src.modules.user.model import User


def format_file_size(size_bytes: int) -> str:
    size = float(size_bytes)
    for unit in ("B", "KB", "MB", "GB"):
        if size < 1024 or unit == "GB":
            return f"{int(size)}B" if unit == "B" else f"{size:.1f}{unit}"
        size /= 1024
    return f"{size_bytes}B"


class KnowledgeService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = KnowledgeBaseRepository(db)
        self.document_repo = DocumentRepository(db)
        self.segment_repo = SegmentRepository(db)
        self.settings = get_settings()

    async def create_base(self, data: KnowledgeBaseCreate, current_user: User) -> KnowledgeBase:
        name = data.name.strip()
        if await self.repo.get_by_name(name):
            raise BizException(code=400, message="知识库名称已存在")
        return await self.repo.create(KnowledgeBase(
            name=name,
            description=data.description.strip() if data.description else None,
            status="empty",
            embedding_model=data.embedding_model.strip(),
            chunk_size=data.chunk_size,
            chunk_overlap=data.chunk_overlap,
            chunk_method=data.chunk_method,
            retrieval_strategy=data.retrieval_strategy,
            top_k=data.top_k,
            similarity_threshold=data.similarity_threshold,
            created_by=current_user.username,
        ))

    async def get_base(self, knowledge_base_id: int) -> KnowledgeBase:
        knowledge_base = await self.repo.get_by_id(knowledge_base_id)
        if not knowledge_base:
            raise BizException(code=404, message="知识库不存在")
        return knowledge_base

    async def search_page(self, offset: int, limit: int, keyword: str | None):
        return await self.repo.search_page(offset, limit, keyword)

    async def update_base(self, knowledge_base_id: int, data: KnowledgeBaseUpdate) -> KnowledgeBase:
        knowledge_base = await self.get_base(knowledge_base_id)
        values = data.model_dump(exclude_unset=True)
        if data.name is not None:
            name = data.name.strip()
            duplicate = await self.repo.get_by_name(name)
            if duplicate and duplicate.id != knowledge_base.id:
                raise BizException(code=400, message="知识库名称已存在")
            knowledge_base.name = name
        if "description" in values:
            knowledge_base.description = data.description.strip() if data.description else None
        if data.embedding_model is not None:
            knowledge_base.embedding_model = data.embedding_model.strip()
        return await self.repo.update(knowledge_base)

    async def update_config(self, knowledge_base_id: int, data: KnowledgeBaseConfigUpdate) -> KnowledgeBase:
        knowledge_base = await self.get_base(knowledge_base_id)
        values = data.model_dump(exclude_unset=True)
        new_size = values.get("chunk_size", knowledge_base.chunk_size)
        new_overlap = values.get("chunk_overlap", knowledge_base.chunk_overlap)
        if new_overlap >= new_size:
            raise BizException(code=400, message="分段重叠必须小于分段大小")
        reprocess = any(key in values for key in ("chunk_size", "chunk_overlap", "chunk_method"))
        for key, value in values.items():
            if key == "embedding_model" and value is not None:
                value = value.strip()
            setattr(knowledge_base, key, value)
        await self.repo.update(knowledge_base)
        if reprocess:
            for document in await self.document_repo.list_for_base(knowledge_base_id):
                try:
                    await process_document_in_session(self.db, document.id)
                except Exception as exc:
                    raise BizException(code=503, message=f"文档重新分段失败：{exc}") from exc
        return knowledge_base

    async def delete_base(self, knowledge_base_id: int) -> None:
        knowledge_base = await self.get_base(knowledge_base_id)
        documents = await self.document_repo.list_for_base(knowledge_base_id)
        try:
            for document in documents:
                if document.minio_path:
                    await asyncio.to_thread(delete_object, document.minio_path)
        except Exception as exc:
            raise BizException(code=503, message=f"MinIO 文档删除失败：{exc}") from exc
        await self.repo.delete(knowledge_base)

    async def list_documents(self, knowledge_base_id: int, offset: int, limit: int, keyword: str | None):
        await self.get_base(knowledge_base_id)
        return await self.document_repo.search_page(knowledge_base_id, offset, limit, keyword)

    async def upload_document(self, knowledge_base_id: int, file: UploadFile, current_user: User) -> Document:
        knowledge_base = await self.get_base(knowledge_base_id)
        original_name = Path(file.filename or "").name
        if not original_name or original_name != (file.filename or ""):
            raise BizException(code=400, message="文件名非法")
        file_type = Path(original_name).suffix.lower().lstrip(".")
        if file_type not in SUPPORTED_DOCUMENT_TYPES:
            raise BizException(code=400, message="仅支持 PDF、DOCX、Markdown、TXT、HTML 和 CSV")
        max_bytes = self.settings.MAX_DOCUMENT_SIZE_MB * 1024 * 1024
        content = await file.read(max_bytes + 1)
        if not content:
            raise BizException(code=400, message="不能上传空文件")
        if len(content) > max_bytes:
            raise BizException(code=400, message=f"文档不能超过 {self.settings.MAX_DOCUMENT_SIZE_MB}MB")

        object_name = f"knowledge-bases/{knowledge_base_id}/{uuid.uuid4().hex}.{file_type}"
        try:
            await asyncio.to_thread(
                upload_file,
                object_name,
                content,
                file.content_type or "application/octet-stream",
            )
        except Exception as exc:
            raise BizException(code=503, message=f"MinIO 文件上传失败：{exc}") from exc

        try:
            document = await self.document_repo.create(Document(
                knowledge_base_id=knowledge_base_id,
                file_name=original_name,
                file_type=file_type,
                file_size=format_file_size(len(content)),
                minio_path=object_name,
                status="pending",
                uploaded_by=current_user.username,
            ))
            await refresh_knowledge_base_counts(self.db, knowledge_base.id)
            return document
        except Exception:
            await asyncio.to_thread(delete_object, object_name)
            raise

    async def get_document(self, knowledge_base_id: int, document_id: int) -> Document:
        await self.get_base(knowledge_base_id)
        document = await self.document_repo.get_for_base(knowledge_base_id, document_id)
        if not document:
            raise BizException(code=404, message="文档不存在")
        return document

    async def delete_document(self, knowledge_base_id: int, document_id: int) -> None:
        document = await self.get_document(knowledge_base_id, document_id)
        if document.minio_path:
            try:
                await asyncio.to_thread(delete_object, document.minio_path)
            except Exception as exc:
                raise BizException(code=503, message=f"MinIO 文档删除失败：{exc}") from exc
        await self.document_repo.delete(document)
        await refresh_knowledge_base_counts(self.db, knowledge_base_id)

    async def retry_document(self, knowledge_base_id: int, document_id: int) -> Document:
        document = await self.get_document(knowledge_base_id, document_id)
        if document.status != "failed":
            raise BizException(code=400, message="只有处理失败的文档可以重试")
        await self.segment_repo.delete_for_document(document.id)
        document.status = "pending"
        document.segment_count = 0
        document.word_count = 0
        document.error_message = None
        document.processed_at = None
        await self.document_repo.update(document)
        await refresh_knowledge_base_counts(self.db, knowledge_base_id)
        return document

    async def list_segments(self, knowledge_base_id: int, offset: int, limit: int, document_id: int | None, keyword: str | None = None):
        await self.get_base(knowledge_base_id)
        if document_id is not None and not await self.document_repo.get_for_base(knowledge_base_id, document_id):
            raise BizException(code=404, message="文档不存在")
        return await self.segment_repo.search_page(knowledge_base_id, offset, limit, document_id, keyword)

    async def update_segment(self, knowledge_base_id: int, segment_id: int, data: SegmentUpdate) -> Segment:
        segment = await self.segment_repo.get_for_base(knowledge_base_id, segment_id)
        if not segment:
            raise BizException(code=404, message="分段不存在")
        content = data.content.strip()
        segment.content = content
        segment.word_count = len(re.findall(r"\S+", content)) if re.search(r"\s", content) else len(content)
        segment.token_count = estimate_tokens(content)
        return await self.segment_repo.update(segment)

    async def retrieval_test(self, knowledge_base_id: int, query: str, top_k: int | None, threshold: float | None):
        knowledge_base = await self.get_base(knowledge_base_id)
        query_value = query.strip()
        query_terms = set(text_terms(query_value))
        if not query_terms:
            raise BizException(code=400, message="查询内容没有可检索词项")
        limit = top_k or knowledge_base.top_k
        cutoff = knowledge_base.similarity_threshold if threshold is None else threshold
        scored = []
        for segment in await self.segment_repo.list_for_retrieval(knowledge_base_id):
            terms = set(text_terms(segment.content))
            overlap = len(query_terms & terms) / len(query_terms)
            exact_bonus = 0.35 if query_value.lower() in segment.content.lower() else 0
            score = min(1.0, overlap * 0.65 + exact_bonus)
            if score >= cutoff:
                scored.append((score, segment))
        selected = sorted(scored, key=lambda item: (-item[0], item[1].id))[:limit]
        results = []
        for score, segment in selected:
            segment.hit_count += 1
            results.append({
                "segment_id": segment.id,
                "document_id": segment.document_id,
                "document_name": segment.document_name,
                "content": segment.content,
                "score": round(score, 4),
                "position": segment.position,
            })
        await self.db.flush()
        return results

"""Background document parsing tasks for MinIO-backed knowledge files."""

import asyncio
import re
from datetime import datetime

from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from src.infra.database import AsyncSessionLocal
from src.infra.minio_client import download_file
from src.modules.knowledge.model import Document, Segment
from src.modules.knowledge.parser import estimate_tokens, extract_text_bytes, split_text
from src.modules.knowledge.repository import DocumentRepository, KnowledgeBaseRepository, SegmentRepository


def _word_count(content: str) -> int:
    return len(re.findall(r"\S+", content)) if re.search(r"\s", content) else len(content)


async def refresh_knowledge_base_counts(db: AsyncSession, knowledge_base_id: int) -> None:
    kb_repo = KnowledgeBaseRepository(db)
    doc_repo = DocumentRepository(db)
    knowledge_base = await kb_repo.get_by_id(knowledge_base_id)
    if not knowledge_base:
        return
    documents = await doc_repo.list_for_base(knowledge_base_id)
    knowledge_base.document_count = len(documents)
    knowledge_base.segment_count = sum(document.segment_count for document in documents)
    if not documents:
        knowledge_base.status = "empty"
    elif any(document.status in {"pending", "processing"} for document in documents):
        knowledge_base.status = "indexing"
    elif any(document.status == "failed" for document in documents):
        knowledge_base.status = "error"
    else:
        knowledge_base.status = "ready"
    await kb_repo.update(knowledge_base)


async def process_document_in_session(db: AsyncSession, document_id: int) -> Document:
    doc_repo = DocumentRepository(db)
    kb_repo = KnowledgeBaseRepository(db)
    seg_repo = SegmentRepository(db)
    document = await doc_repo.get_by_id(document_id)
    if not document:
        raise ValueError("文档不存在")
    knowledge_base = await kb_repo.get_by_id(document.knowledge_base_id)
    if not knowledge_base:
        raise ValueError("知识库不存在")
    if not document.minio_path:
        raise ValueError("文档没有 MinIO 存储路径")

    document.status = "processing"
    document.error_message = None
    await seg_repo.delete_for_document(document.id)
    await doc_repo.update(document)
    await refresh_knowledge_base_counts(db, knowledge_base.id)

    source = await asyncio.to_thread(download_file, document.minio_path)
    text = await asyncio.to_thread(extract_text_bytes, source, document.file_type)
    chunks = split_text(
        text,
        knowledge_base.chunk_method,
        knowledge_base.chunk_size,
        knowledge_base.chunk_overlap,
    )
    if not chunks:
        raise ValueError("未从文档中解析出可用文本")

    await seg_repo.bulk_create([
        Segment(
            knowledge_base_id=knowledge_base.id,
            document_id=document.id,
            position=index,
            content=content,
            word_count=_word_count(content),
            token_count=estimate_tokens(content),
        )
        for index, content in enumerate(chunks, start=1)
    ])
    document.status = "completed"
    document.segment_count = len(chunks)
    document.word_count = _word_count(text)
    document.processed_at = datetime.now()
    await doc_repo.update(document)
    await refresh_knowledge_base_counts(db, knowledge_base.id)
    return document


async def _mark_failed(db: AsyncSession, document_id: int, error: str) -> None:
    document = await db.get(Document, document_id)
    if not document:
        return
    document.status = "failed"
    document.segment_count = 0
    document.word_count = 0
    document.error_message = error[:1000]
    document.processed_at = datetime.now()
    await refresh_knowledge_base_counts(db, document.knowledge_base_id)


async def process_document(document_id: int) -> None:
    """Process one committed document record in a fresh database session."""

    async with AsyncSessionLocal() as db:
        try:
            await process_document_in_session(db, document_id)
            await db.commit()
            logger.info(f"知识文档处理完成 document_id={document_id}")
        except Exception as exc:
            await db.rollback()
            try:
                await _mark_failed(db, document_id, str(exc))
                await db.commit()
            except Exception:
                await db.rollback()
                logger.exception(f"知识文档失败状态写入失败 document_id={document_id}")
            logger.exception(f"知识文档处理失败 document_id={document_id}: {exc}")

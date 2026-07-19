from sqlalchemy import delete, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.base_repository import BaseRepository
from src.modules.knowledge.model import KnowledgeBase, KnowledgeDocument, KnowledgeSegment


class KnowledgeBaseRepository(BaseRepository[KnowledgeBase]):
    def __init__(self, db: AsyncSession):
        super().__init__(KnowledgeBase, db)

    async def get_by_name(self, name: str) -> KnowledgeBase | None:
        return await self.db.scalar(select(KnowledgeBase).where(KnowledgeBase.name == name))

    async def search_page(self, offset: int, limit: int, keyword: str | None) -> tuple[list[KnowledgeBase], int]:
        stmt = select(KnowledgeBase)
        if keyword:
            pattern = f"%{keyword}%"
            stmt = stmt.where(or_(KnowledgeBase.name.like(pattern), KnowledgeBase.description.like(pattern)))
        total = await self.db.scalar(select(func.count()).select_from(stmt.subquery()))
        result = await self.db.execute(stmt.order_by(KnowledgeBase.id.desc()).offset(offset).limit(limit))
        return list(result.scalars().all()), int(total or 0)


class DocumentRepository(BaseRepository[KnowledgeDocument]):
    def __init__(self, db: AsyncSession):
        super().__init__(KnowledgeDocument, db)

    async def get_for_base(self, knowledge_base_id: int, document_id: int) -> KnowledgeDocument | None:
        return await self.db.scalar(select(KnowledgeDocument).where(
            KnowledgeDocument.id == document_id,
            KnowledgeDocument.knowledge_base_id == knowledge_base_id,
        ))

    async def list_for_base(self, knowledge_base_id: int) -> list[KnowledgeDocument]:
        result = await self.db.execute(select(KnowledgeDocument).where(
            KnowledgeDocument.knowledge_base_id == knowledge_base_id
        ).order_by(KnowledgeDocument.id))
        return list(result.scalars().all())

    async def search_page(self, knowledge_base_id: int, offset: int, limit: int, keyword: str | None) -> tuple[list[KnowledgeDocument], int]:
        stmt = select(KnowledgeDocument).where(KnowledgeDocument.knowledge_base_id == knowledge_base_id)
        if keyword:
            stmt = stmt.where(KnowledgeDocument.file_name.like(f"%{keyword}%"))
        total = await self.db.scalar(select(func.count()).select_from(stmt.subquery()))
        result = await self.db.execute(stmt.order_by(KnowledgeDocument.id.desc()).offset(offset).limit(limit))
        return list(result.scalars().all()), int(total or 0)


class SegmentRepository(BaseRepository[KnowledgeSegment]):
    def __init__(self, db: AsyncSession):
        super().__init__(KnowledgeSegment, db)

    async def get_for_base(self, knowledge_base_id: int, segment_id: int) -> KnowledgeSegment | None:
        return await self.db.scalar(select(KnowledgeSegment).where(
            KnowledgeSegment.id == segment_id,
            KnowledgeSegment.knowledge_base_id == knowledge_base_id,
        ))

    async def delete_for_document(self, document_id: int) -> None:
        await self.db.execute(delete(KnowledgeSegment).where(KnowledgeSegment.document_id == document_id))

    async def search_page(
        self,
        knowledge_base_id: int,
        offset: int,
        limit: int,
        document_id: int | None,
        keyword: str | None = None,
    ) -> tuple[list[KnowledgeSegment], int]:
        stmt = select(KnowledgeSegment).where(KnowledgeSegment.knowledge_base_id == knowledge_base_id)
        if document_id is not None:
            stmt = stmt.where(KnowledgeSegment.document_id == document_id)
        if keyword:
            stmt = stmt.where(KnowledgeSegment.content.like(f"%{keyword}%"))
        total = await self.db.scalar(select(func.count()).select_from(stmt.subquery()))
        result = await self.db.execute(
            stmt.order_by(KnowledgeSegment.document_id, KnowledgeSegment.position)
            .offset(offset).limit(limit)
        )
        return list(result.scalars().all()), int(total or 0)

    async def list_for_retrieval(self, knowledge_base_id: int) -> list[KnowledgeSegment]:
        result = await self.db.execute(select(KnowledgeSegment).where(
            KnowledgeSegment.knowledge_base_id == knowledge_base_id
        ))
        return list(result.scalars().all())

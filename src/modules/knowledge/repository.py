from sqlalchemy import delete, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.base_repository import BaseRepository
from src.modules.knowledge.model import Document, KnowledgeBase, Segment


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


class DocumentRepository(BaseRepository[Document]):
    def __init__(self, db: AsyncSession):
        super().__init__(Document, db)

    async def get_for_base(self, knowledge_base_id: int, document_id: int) -> Document | None:
        return await self.db.scalar(select(Document).where(
            Document.id == document_id,
            Document.knowledge_base_id == knowledge_base_id,
        ))

    async def list_for_base(self, knowledge_base_id: int) -> list[Document]:
        result = await self.db.execute(select(Document).where(
            Document.knowledge_base_id == knowledge_base_id
        ).order_by(Document.id))
        return list(result.scalars().all())

    async def search_page(self, knowledge_base_id: int, offset: int, limit: int, keyword: str | None) -> tuple[list[Document], int]:
        stmt = select(Document).where(Document.knowledge_base_id == knowledge_base_id)
        if keyword:
            stmt = stmt.where(Document.file_name.like(f"%{keyword}%"))
        total = await self.db.scalar(select(func.count()).select_from(stmt.subquery()))
        result = await self.db.execute(stmt.order_by(Document.id.desc()).offset(offset).limit(limit))
        return list(result.scalars().all()), int(total or 0)


class SegmentRepository(BaseRepository[Segment]):
    def __init__(self, db: AsyncSession):
        super().__init__(Segment, db)

    async def get_for_base(self, knowledge_base_id: int, segment_id: int) -> Segment | None:
        return await self.db.scalar(select(Segment).where(
            Segment.id == segment_id,
            Segment.knowledge_base_id == knowledge_base_id,
        ))

    async def delete_for_document(self, document_id: int) -> None:
        await self.db.execute(delete(Segment).where(Segment.document_id == document_id))

    async def bulk_create(self, segments: list[Segment]) -> None:
        self.db.add_all(segments)
        await self.db.flush()

    async def search_page(
        self,
        knowledge_base_id: int,
        offset: int,
        limit: int,
        document_id: int | None,
        keyword: str | None = None,
    ) -> tuple[list[Segment], int]:
        stmt = select(Segment).where(Segment.knowledge_base_id == knowledge_base_id)
        if document_id is not None:
            stmt = stmt.where(Segment.document_id == document_id)
        if keyword:
            stmt = stmt.where(Segment.content.like(f"%{keyword}%"))
        total = await self.db.scalar(select(func.count()).select_from(stmt.subquery()))
        result = await self.db.execute(
            stmt.order_by(Segment.document_id, Segment.position).offset(offset).limit(limit)
        )
        return list(result.scalars().all()), int(total or 0)

    async def list_for_retrieval(self, knowledge_base_id: int) -> list[Segment]:
        result = await self.db.execute(select(Segment).where(
            Segment.knowledge_base_id == knowledge_base_id
        ))
        return list(result.scalars().all())

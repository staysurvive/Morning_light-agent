from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.base_model import BaseModel


class KnowledgeBase(BaseModel):
    __tablename__ = "knowledge_bases"

    name: Mapped[str] = mapped_column(String(150), unique=True, index=True, comment="知识库名称")
    description: Mapped[str | None] = mapped_column(String(500), nullable=True, comment="知识库描述")
    status: Mapped[str] = mapped_column(String(20), default="empty", index=True, comment="知识库状态")
    document_count: Mapped[int] = mapped_column(default=0, comment="文档数量")
    segment_count: Mapped[int] = mapped_column(default=0, comment="分段数量")
    embedding_model: Mapped[str] = mapped_column(String(150), default="text-embedding-3-small", comment="Embedding 配置标识")
    chunk_size: Mapped[int] = mapped_column(default=500, comment="分段大小")
    chunk_overlap: Mapped[int] = mapped_column(default=50, comment="分段重叠")
    chunk_method: Mapped[str] = mapped_column(String(20), default="fixed", comment="分段方式")
    retrieval_strategy: Mapped[str] = mapped_column(String(20), default="fulltext", comment="检索策略")
    top_k: Mapped[int] = mapped_column(default=5, comment="默认返回数量")
    similarity_threshold: Mapped[float] = mapped_column(default=0.7, comment="相关度阈值")
    created_by_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="创建人 ID",
    )

    creator = relationship("User", lazy="selectin")
    documents = relationship(
        "KnowledgeDocument",
        back_populates="knowledge_base",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    @property
    def created_by(self) -> str | None:
        return self.creator.username if self.creator else None


class KnowledgeDocument(BaseModel):
    __tablename__ = "knowledge_documents"

    knowledge_base_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("knowledge_bases.id", ondelete="CASCADE"),
        index=True,
        comment="知识库 ID",
    )
    file_name: Mapped[str] = mapped_column(String(255), index=True, comment="原始文件名")
    file_type: Mapped[str] = mapped_column(String(20), comment="文件类型")
    file_size_bytes: Mapped[int] = mapped_column(BigInteger, comment="文件大小（字节）")
    storage_path: Mapped[str] = mapped_column(String(500), unique=True, comment="相对存储路径")
    status: Mapped[str] = mapped_column(String(20), default="pending", index=True, comment="处理状态")
    segment_count: Mapped[int] = mapped_column(default=0, comment="分段数量")
    word_count: Mapped[int] = mapped_column(default=0, comment="字符/词项数量")
    error_message: Mapped[str | None] = mapped_column(String(1000), nullable=True, comment="处理错误")
    uploaded_by_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="上传人 ID",
    )
    uploaded_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, comment="上传时间")
    processed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, comment="处理完成时间")

    knowledge_base = relationship("KnowledgeBase", back_populates="documents")
    uploader = relationship("User", lazy="selectin")
    segments = relationship(
        "KnowledgeSegment",
        back_populates="document",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    @property
    def uploaded_by(self) -> str | None:
        return self.uploader.username if self.uploader else None

    @property
    def file_size(self) -> str:
        size = float(self.file_size_bytes)
        for unit in ("B", "KB", "MB", "GB"):
            if size < 1024 or unit == "GB":
                return f"{size:.1f}{unit}" if unit != "B" else f"{int(size)}B"
            size /= 1024
        return f"{int(self.file_size_bytes)}B"


class KnowledgeSegment(BaseModel):
    __tablename__ = "knowledge_segments"

    knowledge_base_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("knowledge_bases.id", ondelete="CASCADE"),
        index=True,
        comment="知识库 ID",
    )
    document_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("knowledge_documents.id", ondelete="CASCADE"),
        index=True,
        comment="文档 ID",
    )
    content: Mapped[str] = mapped_column(Text, comment="分段内容")
    word_count: Mapped[int] = mapped_column(default=0, comment="字符/词项数量")
    token_count: Mapped[int] = mapped_column(default=0, comment="估算 token 数量")
    position: Mapped[int] = mapped_column(comment="文档内顺序")
    keywords: Mapped[list[str]] = mapped_column(JSON, default=list, comment="关键词")
    hit_count: Mapped[int] = mapped_column(default=0, comment="检索命中次数")

    document = relationship("KnowledgeDocument", back_populates="segments", lazy="selectin")

    @property
    def document_name(self) -> str:
        return self.document.file_name

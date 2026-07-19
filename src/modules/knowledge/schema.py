from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


ChunkMethod = Literal["fixed", "sentence", "paragraph"]
RetrievalStrategy = Literal["fulltext"]


class KnowledgeBaseCreate(BaseModel):
    name: str = Field(min_length=1, max_length=150)
    description: str | None = Field(default=None, max_length=500)
    embedding_model: str = Field(default="text-embedding-3-small", min_length=1, max_length=150)
    chunk_size: int = Field(default=500, ge=100, le=2000)
    chunk_overlap: int = Field(default=50, ge=0, le=500)
    chunk_method: ChunkMethod = "fixed"
    retrieval_strategy: RetrievalStrategy = "fulltext"
    top_k: int = Field(default=5, ge=1, le=20)
    similarity_threshold: float = Field(default=0.7, ge=0, le=1)

    @model_validator(mode="after")
    def validate_overlap(self):
        if self.chunk_overlap >= self.chunk_size:
            raise ValueError("分段重叠必须小于分段大小")
        return self


class KnowledgeBaseUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=150)
    description: str | None = Field(default=None, max_length=500)
    embedding_model: str | None = Field(default=None, min_length=1, max_length=150)


class KnowledgeBaseConfigUpdate(BaseModel):
    embedding_model: str | None = Field(default=None, min_length=1, max_length=150)
    chunk_size: int | None = Field(default=None, ge=100, le=2000)
    chunk_overlap: int | None = Field(default=None, ge=0, le=500)
    chunk_method: ChunkMethod | None = None
    retrieval_strategy: RetrievalStrategy | None = None
    top_k: int | None = Field(default=None, ge=1, le=20)
    similarity_threshold: float | None = Field(default=None, ge=0, le=1)


class KnowledgeBaseRead(BaseModel):
    id: int
    name: str
    description: str | None
    status: Literal["ready", "indexing", "error", "empty"]
    document_count: int
    segment_count: int
    embedding_model: str
    chunk_size: int
    chunk_overlap: int
    chunk_method: ChunkMethod
    retrieval_strategy: RetrievalStrategy
    top_k: int
    similarity_threshold: float
    created_by: str | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DocumentRead(BaseModel):
    id: int
    knowledge_base_id: int
    file_name: str
    file_type: str
    file_size: str
    storage_path: str
    status: Literal["pending", "processing", "completed", "failed"]
    segment_count: int
    word_count: int
    error_message: str | None
    uploaded_by: str | None
    uploaded_at: datetime
    processed_at: datetime | None

    model_config = ConfigDict(from_attributes=True)


class SegmentUpdate(BaseModel):
    content: str = Field(min_length=1)


class SegmentRead(BaseModel):
    id: int
    knowledge_base_id: int
    document_id: int
    document_name: str
    content: str
    word_count: int
    token_count: int
    position: int
    keywords: list[str]
    hit_count: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class RetrievalTestRequest(BaseModel):
    query: str = Field(min_length=1, max_length=1000)
    strategy: RetrievalStrategy | None = None
    top_k: int | None = Field(default=None, ge=1, le=20)
    similarity_threshold: float | None = Field(default=None, ge=0, le=1)


class RetrievalTestResult(BaseModel):
    segment_id: int
    document_id: int
    document_name: str
    content: str
    score: float
    position: int

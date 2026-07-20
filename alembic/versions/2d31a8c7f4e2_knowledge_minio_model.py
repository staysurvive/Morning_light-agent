"""adapt knowledge models to MinIO storage

Revision ID: 2d31a8c7f4e2
Revises: 1ef7a711510b
Create Date: 2026-07-20 17:02:00
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "2d31a8c7f4e2"
down_revision: Union[str, Sequence[str], None] = "1ef7a711510b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _inspector():
    return sa.inspect(op.get_bind())


def _table_exists(name: str) -> bool:
    return name in _inspector().get_table_names()


def _columns(table: str) -> set[str]:
    return {column["name"] for column in _inspector().get_columns(table)}


def _indexes(table: str) -> set[str]:
    return {index["name"] for index in _inspector().get_indexes(table)}


def _drop_fk_for_columns(table: str, columns: list[str]) -> None:
    expected = set(columns)
    for foreign_key in _inspector().get_foreign_keys(table):
        if set(foreign_key["constrained_columns"]) == expected and foreign_key.get("name"):
            op.drop_constraint(foreign_key["name"], table, type_="foreignkey")
            return


def upgrade() -> None:
    if "created_by" not in _columns("knowledge_bases"):
        op.add_column("knowledge_bases", sa.Column("created_by", sa.String(100), nullable=True, comment="创建者"))
    if "created_by_id" in _columns("knowledge_bases"):
        op.execute(sa.text(
            "UPDATE knowledge_bases kb LEFT JOIN users u ON u.id = kb.created_by_id "
            "SET kb.created_by = u.username"
        ))
        _drop_fk_for_columns("knowledge_bases", ["created_by_id"])
        if "ix_knowledge_bases_created_by_id" in _indexes("knowledge_bases"):
            op.drop_index("ix_knowledge_bases_created_by_id", table_name="knowledge_bases")
        op.drop_column("knowledge_bases", "created_by_id")
    op.alter_column("knowledge_bases", "name", existing_type=sa.String(150), type_=sa.String(200), existing_nullable=False, comment="知识库名称")
    op.alter_column("knowledge_bases", "description", existing_type=sa.String(500), existing_nullable=True, comment="描述")
    op.alter_column("knowledge_bases", "status", existing_type=sa.String(20), type_=sa.String(50), existing_nullable=False, comment="状态: ready/indexing/error/empty")
    op.alter_column("knowledge_bases", "embedding_model", existing_type=sa.String(150), type_=sa.String(100), existing_nullable=False, comment="Embedding 配置标识（预留）")
    op.alter_column("knowledge_bases", "chunk_method", existing_type=sa.String(20), existing_nullable=False, comment="分段方式: fixed/sentence/paragraph")
    op.alter_column("knowledge_bases", "chunk_size", existing_type=sa.Integer(), existing_nullable=False, comment="分段大小（tokens）")
    op.alter_column("knowledge_bases", "chunk_overlap", existing_type=sa.Integer(), existing_nullable=False, comment="重叠大小（tokens）")
    op.execute(sa.text("UPDATE knowledge_bases SET retrieval_strategy = 'fulltext'"))
    op.alter_column("knowledge_bases", "retrieval_strategy", existing_type=sa.String(20), existing_nullable=False, comment="检索策略: fulltext")
    op.alter_column("knowledge_bases", "top_k", existing_type=sa.Integer(), existing_nullable=False, comment="返回结果数")
    op.alter_column("knowledge_bases", "similarity_threshold", existing_type=sa.Float(), existing_nullable=False, comment="相似度阈值")

    if _table_exists("knowledge_documents"):
        op.rename_table("knowledge_documents", "documents")
    document_columns = _columns("documents")
    if "file_size" not in document_columns:
        op.add_column("documents", sa.Column("file_size", sa.String(50), nullable=True, comment="文件大小"))
    if "file_size_bytes" in _columns("documents"):
        op.execute(sa.text(
            "UPDATE documents SET file_size = CASE "
            "WHEN file_size_bytes < 1024 THEN CONCAT(file_size_bytes, 'B') "
            "WHEN file_size_bytes < 1048576 THEN CONCAT(ROUND(file_size_bytes / 1024, 1), 'KB') "
            "ELSE CONCAT(ROUND(file_size_bytes / 1048576, 1), 'MB') END"
        ))
        op.drop_column("documents", "file_size_bytes")
    if "uploaded_by" not in _columns("documents"):
        op.add_column("documents", sa.Column("uploaded_by", sa.String(100), nullable=True, comment="上传者"))
    if "uploaded_by_id" in _columns("documents"):
        op.execute(sa.text(
            "UPDATE documents d LEFT JOIN users u ON u.id = d.uploaded_by_id "
            "SET d.uploaded_by = u.username"
        ))
        _drop_fk_for_columns("documents", ["uploaded_by_id"])
        if "ix_knowledge_documents_uploaded_by_id" in _indexes("documents"):
            op.drop_index("ix_knowledge_documents_uploaded_by_id", table_name="documents")
        op.drop_column("documents", "uploaded_by_id")
    if "uploaded_at" in _columns("documents"):
        op.execute(sa.text("UPDATE documents SET created_at = uploaded_at"))
        op.drop_column("documents", "uploaded_at")
    if "storage_path" in _columns("documents"):
        if "storage_path" in _indexes("documents"):
            op.drop_index("storage_path", table_name="documents")
        op.alter_column(
            "documents", "storage_path", new_column_name="minio_path",
            existing_type=sa.String(500), type_=sa.String(1000),
            existing_nullable=False, nullable=True, comment="MinIO 存储路径",
        )
    current_indexes = _indexes("documents")
    if "ix_documents_file_name" not in current_indexes:
        op.create_index("ix_documents_file_name", "documents", ["file_name"])
    if "ix_documents_knowledge_base_id" not in current_indexes:
        op.create_index("ix_documents_knowledge_base_id", "documents", ["knowledge_base_id"])
    if "ix_documents_status" not in current_indexes:
        op.create_index("ix_documents_status", "documents", ["status"])
    for old_name in (
        "ix_knowledge_documents_file_name",
        "ix_knowledge_documents_knowledge_base_id",
        "ix_knowledge_documents_status",
    ):
        if old_name in _indexes("documents"):
            op.drop_index(old_name, table_name="documents")
    op.alter_column("documents", "knowledge_base_id", existing_type=sa.BigInteger(), existing_nullable=False, comment="所属知识库ID")
    op.alter_column("documents", "file_name", existing_type=sa.String(255), type_=sa.String(500), existing_nullable=False, comment="文件名")
    op.alter_column("documents", "file_type", existing_type=sa.String(20), type_=sa.String(50), existing_nullable=False, comment="文件类型: pdf/docx/md/txt/html/csv")
    op.alter_column("documents", "status", existing_type=sa.String(20), type_=sa.String(50), existing_nullable=False, comment="处理状态: pending/processing/completed/failed")
    op.alter_column("documents", "segment_count", existing_type=sa.Integer(), existing_nullable=False, comment="分段数量")
    op.alter_column("documents", "word_count", existing_type=sa.Integer(), existing_nullable=False, comment="字数")
    op.alter_column("documents", "error_message", existing_type=sa.String(1000), type_=sa.Text(), existing_nullable=True, comment="错误信息")
    op.alter_column("documents", "processed_at", existing_type=sa.DateTime(), existing_nullable=True, comment="处理完成时间")

    if _table_exists("knowledge_segments"):
        op.rename_table("knowledge_segments", "segments")
    current_indexes = _indexes("segments")
    if "ix_segments_document_id" not in current_indexes:
        op.create_index("ix_segments_document_id", "segments", ["document_id"])
    if "ix_segments_knowledge_base_id" not in current_indexes:
        op.create_index("ix_segments_knowledge_base_id", "segments", ["knowledge_base_id"])
    for old_name in ("ix_knowledge_segments_document_id", "ix_knowledge_segments_knowledge_base_id"):
        if old_name in _indexes("segments"):
            op.drop_index(old_name, table_name="segments")
    if "keywords" in _columns("segments"):
        op.drop_column("segments", "keywords")
    op.alter_column("segments", "knowledge_base_id", existing_type=sa.BigInteger(), existing_nullable=False, comment="所属知识库ID")
    op.alter_column("segments", "document_id", existing_type=sa.BigInteger(), existing_nullable=False, comment="所属文档ID")
    op.alter_column("segments", "position", existing_type=sa.Integer(), existing_nullable=False, comment="在文档中的位置序号")
    op.alter_column("segments", "content", existing_type=sa.Text(), existing_nullable=False, comment="分段内容")
    op.alter_column("segments", "word_count", existing_type=sa.Integer(), existing_nullable=False, comment="字数")
    op.alter_column("segments", "token_count", existing_type=sa.Integer(), existing_nullable=False, comment="Token 数")
    op.alter_column("segments", "hit_count", existing_type=sa.Integer(), existing_nullable=False, comment="检索命中次数")


def downgrade() -> None:
    op.add_column("segments", sa.Column("keywords", sa.JSON(), nullable=True, comment="关键词"))
    op.rename_table("segments", "knowledge_segments")
    op.alter_column(
        "documents", "minio_path", new_column_name="storage_path",
        existing_type=sa.String(1000), type_=sa.String(500),
        existing_nullable=True, nullable=False, comment="相对存储路径",
    )
    op.add_column("documents", sa.Column("file_size_bytes", sa.BigInteger(), nullable=False, server_default="0", comment="文件大小（字节）"))
    op.add_column("documents", sa.Column("uploaded_by_id", sa.BigInteger(), nullable=True, comment="上传人 ID"))
    op.add_column("documents", sa.Column("uploaded_at", sa.DateTime(), nullable=False, server_default=sa.text("now()"), comment="上传时间"))
    op.rename_table("documents", "knowledge_documents")
    op.add_column("knowledge_bases", sa.Column("created_by_id", sa.BigInteger(), nullable=True, comment="创建人 ID"))
    op.drop_column("knowledge_bases", "created_by")

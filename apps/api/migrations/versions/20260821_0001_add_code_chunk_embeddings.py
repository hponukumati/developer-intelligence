"""Add pgvector support for code chunks.

Revision ID: 20260821_0001
Revises:
Create Date: 2026-08-21
"""
from alembic import op

revision = "20260821_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.execute("ALTER TABLE code_chunks ADD COLUMN IF NOT EXISTS embedding vector(1536)")
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_code_chunks_embedding_hnsw "
        "ON code_chunks USING hnsw (embedding vector_cosine_ops) WITH (m = 16, ef_construction = 64)"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_code_chunks_embedding_hnsw")
    op.execute("ALTER TABLE code_chunks DROP COLUMN IF EXISTS embedding")

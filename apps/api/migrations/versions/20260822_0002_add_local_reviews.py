"""Add persisted local review evidence.

Revision ID: 20260822_0002
Revises: 20260821_0001
Create Date: 2026-08-22
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "20260822_0002"
down_revision = "20260821_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "local_reviews",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("repository_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("pull_request_number", sa.Integer(), nullable=True),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("patch", sa.Text(), nullable=False),
        sa.Column("evidence", postgresql.JSONB(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["repository_id"], ["repositories.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_local_reviews_organization_id", "local_reviews", ["organization_id"])
    op.create_index("ix_local_reviews_repository_id", "local_reviews", ["repository_id"])


def downgrade() -> None:
    op.drop_index("ix_local_reviews_repository_id", table_name="local_reviews")
    op.drop_index("ix_local_reviews_organization_id", table_name="local_reviews")
    op.drop_table("local_reviews")

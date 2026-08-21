from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.repository import CodeChunk, Repository
from app.retrieval.embeddings import build_embedding_provider
from app.services.runtime_embeddings import runtime_embedding_settings


def index_repository_embeddings(db: Session, repository: Repository, organization_id: uuid.UUID) -> int:
    state = runtime_embedding_settings.read()
    if not state.embedding_calls_enabled:
        raise RuntimeError("Embedding calls are disabled")
    provider = runtime_embedding_settings.provider()
    chunks = db.execute(select(CodeChunk).where(CodeChunk.repository_id == repository.id, CodeChunk.organization_id == organization_id)).scalars().all()
    vectors = provider.embed([chunk.content for chunk in chunks])
    for chunk, vector in zip(chunks, vectors):
        if len(vector) != 1536:
            raise RuntimeError("Embedding provider returned an unexpected dimension")
        chunk.embedding = vector
    db.commit()
    return len(chunks)

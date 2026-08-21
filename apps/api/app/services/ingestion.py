from __future__ import annotations

import hashlib
import uuid

from sqlalchemy import delete
from sqlalchemy.orm import Session

from app.models.repository import CodeChunk, Repository, RepositoryStatus
from app.retrieval.chunker import chunk_document


def ingest_document(
    db: Session,
    repository: Repository,
    organization_id: uuid.UUID,
    file_path: str,
    content: str,
) -> int:
    """Replace one file atomically, always enforcing repo and org ownership."""
    chunks = chunk_document(file_path, content)
    if not chunks:
        return 0
    db.execute(
        delete(CodeChunk).where(
            CodeChunk.repository_id == repository.id,
            CodeChunk.organization_id == organization_id,
            CodeChunk.file_path == file_path,
        )
    )
    for chunk in chunks:
        db.add(
            CodeChunk(
                organization_id=organization_id,
                repository_id=repository.id,
                file_path=file_path,
                language=chunk.language,
                symbol_name=chunk.symbol_name,
                symbol_type=chunk.symbol_type,
                start_line=chunk.start_line,
                end_line=chunk.end_line,
                content=chunk.content,
                content_hash=hashlib.sha256(chunk.content.encode("utf-8")).hexdigest(),
                metadata_={"ingestion_source": "local_api"},
            )
        )
    repository.status = RepositoryStatus.READY
    db.commit()
    return len(chunks)

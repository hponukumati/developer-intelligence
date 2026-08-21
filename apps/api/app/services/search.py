import time
from sqlalchemy import Select, select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.repository import CodeChunk
from app.schemas.search import SearchRequest, SearchResponse, SearchResult


def _scoped_chunks(request: SearchRequest, organization_id) -> Select:
    statement = select(CodeChunk).where(
        CodeChunk.repository_id == request.repository_id,
        CodeChunk.organization_id == organization_id,
    )
    if request.filters.language:
        statement = statement.where(CodeChunk.language == request.filters.language)
    if request.filters.path_prefix:
        statement = statement.where(CodeChunk.file_path.startswith(request.filters.path_prefix))
    if request.filters.symbol_type:
        statement = statement.where(CodeChunk.symbol_type == request.filters.symbol_type)
    return statement


def search_chunks(db: Session, request: SearchRequest, organization_id) -> SearchResponse:
    """Safe lexical baseline; semantic/RRF is added once embeddings are wired.

    Never silently broaden the org/repository scope, even for zero-result queries.
    """
    started = time.perf_counter()
    # PostgreSQL full-text search will replace this portable baseline in the next milestone.
    terms = [term for term in request.query.split() if len(term) > 1][:12]
    statement = _scoped_chunks(request, organization_id)
    for term in terms:
        statement = statement.where(CodeChunk.content.ilike(f"%{term}%"))
    chunks = db.execute(statement.limit(request.limit)).scalars().all()
    results = [
        SearchResult(
            chunk_id=chunk.id,
            file_path=chunk.file_path,
            start_line=chunk.start_line,
            end_line=chunk.end_line,
            score=1.0 / (index + 1),
            content=chunk.content,
        )
        for index, chunk in enumerate(chunks)
    ]
    return SearchResponse(
        query=request.query,
        latency_ms=int((time.perf_counter() - started) * 1_000),
        # Never present lexical results as semantic/hybrid matches while embeddings are disabled.
        effective_mode="keyword" if not get_settings().enable_live_embeddings else request.mode.value,
        semantic_enabled=get_settings().enable_live_embeddings,
        results=results,
    )

import time
from sqlalchemy import Select, select
from sqlalchemy.orm import Session

from app.models.repository import CodeChunk
from app.retrieval.fusion import reciprocal_rank_fusion
from app.schemas.search import SearchRequest, SearchResponse, SearchResult
from app.services.runtime_embeddings import runtime_embedding_settings


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
    keyword_chunks = db.execute(statement.limit(request.limit)).scalars().all()
    # Vector candidates are intentionally absent until approved embeddings are generated.
    # Keep RRF in the pipeline now so the source integration is an additive change later.
    fused = reciprocal_rank_fusion([[chunk.id for chunk in keyword_chunks]])
    chunks_by_id = {chunk.id: chunk for chunk in keyword_chunks}
    chunks = [(chunks_by_id[chunk_id], score) for chunk_id, score in fused]
    results = [
        SearchResult(
            chunk_id=chunk.id,
            file_path=chunk.file_path,
            start_line=chunk.start_line,
            end_line=chunk.end_line,
            score=score,
            content=chunk.content,
        )
        for chunk, score in chunks
    ]
    return SearchResponse(
        query=request.query,
        latency_ms=int((time.perf_counter() - started) * 1_000),
        # Never present lexical results as semantic/hybrid matches while embeddings are disabled.
        effective_mode="keyword",
        # The toggle permits provider calls, but semantic retrieval remains unavailable
        # until pgvector indexing/RRF is implemented.
        semantic_enabled=False,
        results=results,
    )

import time
from collections.abc import Sequence

from sqlalchemy import Select, select
from sqlalchemy.orm import Session

from app.models.repository import CodeChunk
from app.retrieval.fusion import reciprocal_rank_fusion
from app.schemas.search import SearchMode, SearchRequest, SearchResponse, SearchResult
from app.services.runtime_embeddings import runtime_embedding_settings


class SemanticSearchUnavailable(RuntimeError):
    """Raised when a caller requests semantic retrieval without its local gate enabled."""


class SemanticSearchProviderError(RuntimeError):
    """Raised without exposing provider details to API clients."""


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


def _keyword_candidates(db: Session, request: SearchRequest, organization_id) -> list[CodeChunk]:
    terms = [term for term in request.query.split() if len(term) > 1][:12]
    statement = _scoped_chunks(request, organization_id)
    for term in terms:
        statement = statement.where(CodeChunk.content.ilike(f"%{term}%"))
    return list(db.execute(statement.limit(request.limit)).scalars().all())


def _semantic_candidates(db: Session, request: SearchRequest, organization_id) -> list[CodeChunk]:
    state = runtime_embedding_settings.read()
    if not state.embedding_calls_enabled:
        raise SemanticSearchUnavailable("Semantic search requires explicitly enabled local embedding calls")

    try:
        vectors = runtime_embedding_settings.provider().embed([request.query])
    except Exception as error:
        # Provider exceptions can include infrastructure details. Keep them out of the API response.
        raise SemanticSearchProviderError("The configured embedding provider could not complete the search") from error

    if len(vectors) != 1 or len(vectors[0]) != 1536:
        raise SemanticSearchProviderError("The configured embedding provider returned an invalid search vector")

    statement = _scoped_chunks(request, organization_id).where(CodeChunk.embedding.is_not(None))
    statement = statement.order_by(CodeChunk.embedding.cosine_distance(vectors[0]))
    candidate_limit = min(request.limit * 4, 100)
    return list(db.execute(statement.limit(candidate_limit)).scalars().all())


def search_chunks(db: Session, request: SearchRequest, organization_id) -> SearchResponse:
    """Return only repository- and organization-scoped keyword/vector candidates."""
    started = time.perf_counter()
    keyword_chunks: Sequence[CodeChunk] = []
    semantic_chunks: Sequence[CodeChunk] = []
    semantic_enabled = False

    if request.mode in (SearchMode.KEYWORD, SearchMode.HYBRID):
        keyword_chunks = _keyword_candidates(db, request, organization_id)
    if request.mode in (SearchMode.SEMANTIC, SearchMode.HYBRID):
        semantic_enabled = runtime_embedding_settings.read().embedding_calls_enabled
        if not semantic_enabled and request.mode == SearchMode.SEMANTIC:
            raise SemanticSearchUnavailable("Semantic search requires explicitly enabled local embedding calls")
        if semantic_enabled:
            try:
                semantic_chunks = _semantic_candidates(db, request, organization_id)
            except SemanticSearchProviderError:
                if request.mode == SearchMode.SEMANTIC:
                    raise
                semantic_enabled = False

    ranked_lists = []
    if keyword_chunks:
        ranked_lists.append([chunk.id for chunk in keyword_chunks])
    if semantic_chunks:
        ranked_lists.append([chunk.id for chunk in semantic_chunks])
    fused = reciprocal_rank_fusion(ranked_lists)
    chunks_by_id = {chunk.id: chunk for chunk in [*keyword_chunks, *semantic_chunks]}
    chunks = [(chunks_by_id[chunk_id], score) for chunk_id, score in fused[: request.limit]]
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
        effective_mode=request.mode.value if semantic_enabled else SearchMode.KEYWORD.value,
        semantic_enabled=semantic_enabled,
        results=results,
    )

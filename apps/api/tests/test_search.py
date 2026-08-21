from types import SimpleNamespace
from uuid import uuid4

import pytest
from sqlalchemy.dialects import postgresql

from app.schemas.search import SearchMode, SearchRequest
from app.services import search


def _request(mode: SearchMode) -> SearchRequest:
    return SearchRequest(query="retry payment", repository_id=uuid4(), mode=mode)


def _chunk():
    return SimpleNamespace(
        id=uuid4(),
        file_path="src/payments.py",
        start_line=10,
        end_line=12,
        content="def retry_payment(): pass",
    )


def test_keyword_mode_never_uses_embedding_provider(monkeypatch):
    monkeypatch.setattr(search, "_keyword_candidates", lambda *_: [_chunk()])
    monkeypatch.setattr(search.runtime_embedding_settings, "provider", lambda: pytest.fail("provider must not be called"))

    response = search.search_chunks(object(), _request(SearchMode.KEYWORD), uuid4())

    assert response.effective_mode == "keyword"
    assert response.semantic_enabled is False
    assert len(response.results) == 1


def test_semantic_mode_requires_enabled_gate(monkeypatch):
    monkeypatch.setattr(
        search.runtime_embedding_settings,
        "read",
        lambda: SimpleNamespace(embedding_calls_enabled=False),
    )
    monkeypatch.setattr(search.runtime_embedding_settings, "provider", lambda: pytest.fail("provider must not be called"))

    with pytest.raises(search.SemanticSearchUnavailable):
        search.search_chunks(object(), _request(SearchMode.SEMANTIC), uuid4())


def test_hybrid_mode_falls_back_without_outbound_call_when_gate_is_disabled(monkeypatch):
    monkeypatch.setattr(search, "_keyword_candidates", lambda *_: [_chunk()])
    monkeypatch.setattr(
        search.runtime_embedding_settings,
        "read",
        lambda: SimpleNamespace(embedding_calls_enabled=False),
    )
    monkeypatch.setattr(search, "_semantic_candidates", lambda *_: pytest.fail("semantic search must not run"))

    response = search.search_chunks(object(), _request(SearchMode.HYBRID), uuid4())

    assert response.effective_mode == "keyword"
    assert response.semantic_enabled is False
    assert len(response.results) == 1


def test_semantic_query_is_scoped_to_indexed_chunks_and_uses_bounded_candidate_pool(monkeypatch):
    captured = []

    class Result:
        def scalars(self):
            return self

        def all(self):
            return []

    class Session:
        def execute(self, statement):
            captured.append(statement)
            return Result()

    class Provider:
        def embed(self, texts):
            assert texts == ["retry payment"]
            return [[0.0] * 1536]

    monkeypatch.setattr(
        search.runtime_embedding_settings,
        "read",
        lambda: SimpleNamespace(embedding_calls_enabled=True),
    )
    monkeypatch.setattr(search.runtime_embedding_settings, "provider", lambda: Provider())
    request = _request(SearchMode.SEMANTIC).model_copy(update={"limit": 25})

    assert search._semantic_candidates(Session(), request, uuid4()) == []
    compiled = str(captured[0].compile(dialect=postgresql.dialect()))
    assert "organization_id" in compiled
    assert "repository_id" in compiled
    assert "embedding IS NOT NULL" in compiled
    assert "embedding <=>" in compiled
    assert captured[0]._limit_clause.value == 100


def test_semantic_query_rejects_invalid_provider_vector(monkeypatch):
    class Provider:
        def embed(self, _texts):
            return [[0.0] * 8]

    monkeypatch.setattr(
        search.runtime_embedding_settings,
        "read",
        lambda: SimpleNamespace(embedding_calls_enabled=True),
    )
    monkeypatch.setattr(search.runtime_embedding_settings, "provider", lambda: Provider())

    with pytest.raises(search.SemanticSearchProviderError):
        search._semantic_candidates(object(), _request(SearchMode.SEMANTIC), uuid4())

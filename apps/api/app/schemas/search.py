from __future__ import annotations

import enum
import uuid
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class SearchMode(str, enum.Enum):
    KEYWORD = "keyword"
    SEMANTIC = "semantic"
    HYBRID = "hybrid"


class SearchFilters(BaseModel):
    language: Optional[str] = Field(default=None, max_length=64)
    path_prefix: Optional[str] = Field(default=None, max_length=512)
    symbol_type: Optional[str] = Field(default=None, max_length=64)

    @field_validator("path_prefix")
    @classmethod
    def validate_path_prefix(cls, value: Optional[str]) -> Optional[str]:
        if value and (value.startswith("/") or ".." in value or "\x00" in value):
            raise ValueError("invalid path prefix")
        return value


class SearchRequest(BaseModel):
    query: str = Field(min_length=2, max_length=2_000)
    repository_id: uuid.UUID
    limit: int = Field(default=10, ge=1, le=25)
    mode: SearchMode = SearchMode.HYBRID
    filters: SearchFilters = Field(default_factory=SearchFilters)


class SearchResult(BaseModel):
    chunk_id: uuid.UUID
    file_path: str
    start_line: int
    end_line: int
    score: float
    content: str


class SearchResponse(BaseModel):
    query: str
    latency_ms: int
    effective_mode: str
    semantic_enabled: bool
    results: list[SearchResult]

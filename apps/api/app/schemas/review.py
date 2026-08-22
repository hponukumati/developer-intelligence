from __future__ import annotations

import enum
import uuid
from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field, field_validator


class FindingCategory(str, enum.Enum):
    CORRECTNESS = "correctness"
    SECURITY = "security"
    PERFORMANCE = "performance"
    CONCURRENCY = "concurrency"
    ERROR_HANDLING = "error_handling"
    MAINTAINABILITY = "maintainability"
    TESTING = "testing"


class FindingSeverity(str, enum.Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class ReviewRequest(BaseModel):
    repository_id: uuid.UUID
    pull_request_number: Optional[int] = Field(default=None, ge=1, le=10_000_000)
    title: str = Field(default="Local patch review", min_length=1, max_length=200)
    patch: str = Field(min_length=1, max_length=1_048_576)

    @field_validator("patch")
    @classmethod
    def require_unified_diff_marker(cls, value: str) -> str:
        if "+++ " not in value or "@@ " not in value:
            raise ValueError("patch must contain a unified diff file and hunk header")
        return value


class ReviewEvidence(BaseModel):
    status: Literal["matched", "no_local_context"]
    changed_file_path: str
    changed_start_line: int
    changed_end_line: int
    chunk_id: Optional[uuid.UUID] = None
    file_path: Optional[str] = None
    start_line: Optional[int] = None
    end_line: Optional[int] = None
    excerpt: Optional[str] = Field(default=None, max_length=1_000)


class ReviewAccepted(BaseModel):
    review_id: uuid.UUID
    status: str
    message: str


class ReviewRead(BaseModel):
    review_id: uuid.UUID
    repository_id: uuid.UUID
    pull_request_number: Optional[int]
    title: str
    status: str
    evidence: list[ReviewEvidence]
    created_at: datetime

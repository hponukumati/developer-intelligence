from __future__ import annotations

import re
import uuid

from pydantic import BaseModel, ConfigDict, Field, field_validator

GITHUB_NAME = re.compile(r"^[A-Za-z0-9_.-]{1,100}$")
BRANCH_NAME = re.compile(r"^[A-Za-z0-9._/-]{1,255}$")


class RepositoryCreate(BaseModel):
    provider: str = Field(default="local", pattern="^(local|github)$")
    owner: str = Field(min_length=1, max_length=100)
    repository: str = Field(min_length=1, max_length=100)
    branch: str = Field(default="main", min_length=1, max_length=255)

    @field_validator("owner", "repository")
    @classmethod
    def validate_github_name(cls, value: str) -> str:
        if not GITHUB_NAME.fullmatch(value):
            raise ValueError("must contain only GitHub-safe name characters")
        return value

    @field_validator("branch")
    @classmethod
    def validate_branch(cls, value: str) -> str:
        if not BRANCH_NAME.fullmatch(value) or ".." in value or value.startswith("/"):
            raise ValueError("invalid branch name")
        return value


class RepositoryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    provider: str
    owner: str
    name: str
    branch: str
    status: str


class IndexJobAccepted(BaseModel):
    repository: RepositoryRead
    message: str


class DocumentIngest(BaseModel):
    """A local-only document payload; GitHub fetching is intentionally separate."""

    file_path: str = Field(min_length=1, max_length=1_024)
    content: str = Field(min_length=1, max_length=1_048_576)

    @field_validator("file_path")
    @classmethod
    def validate_file_path(cls, value: str) -> str:
        normalized = value.replace("\\", "/")
        parts = normalized.split("/")
        if (
            normalized.startswith("/")
            or "\x00" in normalized
            or any(part in {"", ".", ".."} for part in parts)
        ):
            raise ValueError("file path must be a relative, normalized path")
        return normalized


class IngestResult(BaseModel):
    repository_id: uuid.UUID
    file_path: str
    chunks_created: int
    status: str

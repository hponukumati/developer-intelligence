"""Local review evidence generation; no fetches, agent calls, or repository execution."""
from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.repository import CodeChunk, Repository
from app.models.review import LocalReview
from app.schemas.review import ReviewEvidence, ReviewRead
from app.services.local_review import ChangedHunk, parse_unified_diff

MAX_CONTEXTS_PER_HUNK = 3


def _evidence_for_hunk(
    db: Session,
    repository: Repository,
    organization_id: uuid.UUID,
    hunk: ChangedHunk,
) -> list[ReviewEvidence]:
    statement = (
        select(CodeChunk)
        .where(
            CodeChunk.organization_id == organization_id,
            CodeChunk.repository_id == repository.id,
            CodeChunk.file_path == hunk.file_path,
            CodeChunk.start_line <= hunk.end_line,
            CodeChunk.end_line >= hunk.start_line,
        )
        .order_by(CodeChunk.start_line, CodeChunk.id)
        .limit(MAX_CONTEXTS_PER_HUNK)
    )
    chunks = db.execute(statement).scalars().all()
    if not chunks:
        return [
            ReviewEvidence(
                status="no_local_context",
                changed_file_path=hunk.file_path,
                changed_start_line=hunk.start_line,
                changed_end_line=hunk.end_line,
            )
        ]
    return [
        ReviewEvidence(
            status="matched",
            changed_file_path=hunk.file_path,
            changed_start_line=hunk.start_line,
            changed_end_line=hunk.end_line,
            chunk_id=chunk.id,
            file_path=chunk.file_path,
            start_line=chunk.start_line,
            end_line=chunk.end_line,
            excerpt=chunk.content[:1_000],
        )
        for chunk in chunks
    ]


def create_local_review(
    db: Session,
    repository: Repository,
    organization_id: uuid.UUID,
    title: str,
    pull_request_number: int | None,
    patch: str,
) -> LocalReview:
    evidence = [
        item.model_dump(mode="json")
        for hunk in parse_unified_diff(patch)
        for item in _evidence_for_hunk(db, repository, organization_id, hunk)
    ]
    review = LocalReview(
        organization_id=organization_id,
        repository_id=repository.id,
        pull_request_number=pull_request_number,
        title=title,
        patch=patch,
        evidence=evidence,
    )
    db.add(review)
    db.commit()
    db.refresh(review)
    return review


def to_review_read(review: LocalReview) -> ReviewRead:
    return ReviewRead(
        review_id=review.id,
        repository_id=review.repository_id,
        pull_request_number=review.pull_request_number,
        title=review.title,
        status=review.status,
        evidence=[ReviewEvidence.model_validate(item) for item in review.evidence],
        created_at=review.created_at,
    )

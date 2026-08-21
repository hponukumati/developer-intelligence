import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.repository import Repository, RepositoryStatus
from app.schemas.repository import DocumentIngest, IndexJobAccepted, IngestResult, RepositoryCreate, RepositoryRead
from app.schemas.review import ReviewAccepted, ReviewRequest
from app.schemas.search import SearchRequest, SearchResponse
from app.schemas.settings import EmbeddingSettingsRead, EmbeddingSettingsUpdate
from app.services.search import search_chunks
from app.services.ingestion import ingest_document
from app.services.runtime_embeddings import runtime_embedding_settings
from app.services.tenant import current_organization_id

router = APIRouter(prefix="/api")


def _require_development_mode() -> None:
    from app.core.config import get_settings

    if get_settings().environment != "development":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Runtime provider configuration is disabled outside local development")


@router.get("/settings/embeddings", response_model=EmbeddingSettingsRead)
def get_embedding_settings() -> EmbeddingSettingsRead:
    _require_development_mode()
    return runtime_embedding_settings.read()


@router.put("/settings/embeddings", response_model=EmbeddingSettingsRead)
def update_embedding_settings(payload: EmbeddingSettingsUpdate) -> EmbeddingSettingsRead:
    _require_development_mode()
    return runtime_embedding_settings.update(payload)


@router.post("/repositories", response_model=IndexJobAccepted, status_code=status.HTTP_202_ACCEPTED)
def create_repository(payload: RepositoryCreate, db: Session = Depends(get_db)):
    """Register indexing work only; cloning is intentionally not done in an HTTP request."""
    repository = Repository(
        organization_id=current_organization_id(),
        provider=payload.provider,
        owner=payload.owner,
        name=payload.repository,
        branch=payload.branch,
        status=RepositoryStatus.PENDING,
    )
    db.add(repository)
    db.commit()
    db.refresh(repository)
    return IndexJobAccepted(
        repository=RepositoryRead.model_validate(repository),
        message="Repository accepted. Ingest user-supplied documents through the local ingestion endpoint.",
    )


@router.post("/repositories/{repository_id}/documents", response_model=IngestResult)
def ingest_local_document(repository_id: uuid.UUID, payload: DocumentIngest, db: Session = Depends(get_db)):
    """Ingest user-supplied content only. It does not fetch paths or call GitHub."""
    organization_id = current_organization_id()
    repository = db.get(Repository, repository_id)
    if repository is None or repository.organization_id != organization_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Repository not found")
    chunks_created = ingest_document(db, repository, organization_id, payload.file_path, payload.content)
    return IngestResult(
        repository_id=repository.id,
        file_path=payload.file_path,
        chunks_created=chunks_created,
        status=repository.status.value,
    )


@router.post("/search", response_model=SearchResponse)
def search(payload: SearchRequest, db: Session = Depends(get_db)):
    repository = db.get(Repository, payload.repository_id)
    if repository is None or repository.organization_id != current_organization_id():
        # Intentionally identical response for missing and unauthorized resources.
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Repository not found")
    return search_chunks(db, payload, current_organization_id())


@router.post("/reviews", response_model=ReviewAccepted, status_code=status.HTTP_202_ACCEPTED)
def create_review(payload: ReviewRequest, db: Session = Depends(get_db)):
    repository = db.get(Repository, payload.repository_id)
    if repository is None or repository.organization_id != current_organization_id():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Repository not found")
    return ReviewAccepted(
        review_id=uuid.uuid4(),
        status="QUEUED",
        message="Review accepted. PR fetching and agent execution are not enabled yet.",
    )

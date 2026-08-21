import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.repository import Repository, RepositoryStatus
from app.schemas.repository import DocumentIngest, IndexJobAccepted, IngestResult, RepositoryCreate, RepositoryRead
from app.schemas.review import ReviewAccepted, ReviewRequest
from app.schemas.search import SearchRequest, SearchResponse
from app.services.search import search_chunks
from app.services.ingestion import ingest_document
from app.services.tenant import current_organization_id

router = APIRouter(prefix="/api")


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

import enum
import uuid

from pydantic import BaseModel, Field


class FindingCategory(str, enum.Enum):
    CORRECTNESS = "correctness"
    SECURITY = "security"
    PERFORMANCE = "performance"
    CONCURRENCY = "concurrency"
    ERROR_HANDLING = "error_handling"
    MAINTAINABILITY = "maintainability"
    TESTING = "testing"


class ReviewRequest(BaseModel):
    repository_id: uuid.UUID
    pull_request_number: int = Field(ge=1, le=10_000_000)


class ReviewAccepted(BaseModel):
    review_id: uuid.UUID
    status: str
    message: str

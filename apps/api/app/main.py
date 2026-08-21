from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.api.routes import router
from app.core.config import get_settings
from app.core.database import Base, engine
from app.models.repository import CodeChunk, Repository  # noqa: F401

settings = get_settings()
app = FastAPI(title=settings.app_name, version="0.1.0", docs_url="/docs" if settings.environment == "development" else None)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[str(origin) for origin in settings.api_cors_origins],
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "Authorization"],
)
app.include_router(router)


@app.on_event("startup")
def create_local_tables() -> None:
    # New local databases need the extension before SQLAlchemy creates vector columns.
    with engine.begin() as connection:
        connection.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
    # Alembic owns non-additive schema changes; this bootstraps an empty local database.
    Base.metadata.create_all(bind=engine)


@app.get("/health", tags=["health"])
def health() -> dict[str, str]:
    return {"status": "ok", "environment": settings.environment}

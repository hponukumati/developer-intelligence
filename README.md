# Developer Intelligence

Local-first MVP for hybrid code search and evidence-backed pull-request reviews.

## Current milestone

The initial foundation includes a FastAPI service, PostgreSQL with pgvector, repository and review schemas, secure request validation, and a Next.js search/dashboard shell. GitHub OAuth, webhooks, automatic comments, and public deployment are deliberately deferred until a security-review checkpoint.

## Local development

1. Copy `.env.example` to `.env`, then set a unique local PostgreSQL password.
2. Start the API and database: `docker compose up --build`.
3. In a separate terminal: `cd apps/web && npm install && npm run dev`.
4. Browse to `http://localhost:3000`; API documentation is at `http://localhost:8000/docs`.

The Docker ports bind to loopback only. Do not add real provider or GitHub credentials until the relevant integration is implemented and reviewed.

## Current API flow

The current API supports a local-only code-search workflow:

1. `POST /api/repositories` with `provider: "local"` creates a repository record.
2. `POST /api/repositories/{repository_id}/documents` accepts bounded source text and a normalized relative path.
3. `POST /api/search` performs repository- and tenant-scoped keyword search.

The document endpoint does not access the filesystem, clone URLs, or contact GitHub. Python is chunked by top-level functions/classes; other supported text/code formats use bounded line chunks.

## Embedding provider gate

The provider interface includes a disabled adapter and an OpenAI-compatible adapter. The local UI may enable provider calls only after a user enters a key and explicitly confirms external data transfer/cost. The key is held in API process memory only (not in browser storage, `.env`, logs, database, or API responses) and is cleared when disabled or the API restarts. Runtime configuration is blocked outside `development`. While semantic retrieval is unfinished, search reports `effective_mode: "keyword"` rather than claiming semantic or hybrid results.

## Hybrid retrieval foundation

`code_chunks.embedding` is a pgvector(1536) column with an HNSW cosine index. The migration is available through `docker-compose --profile tools run --rm migrate`. Keyword candidates already flow through Reciprocal Rank Fusion (RRF); vector candidates will join that same pipeline only after an approved embedding run creates them.

## Security posture

- No secrets in source control; `.env` is ignored.
- Database and API are local-only by default.
- Repository references, URLs, request sizes, and enum values are validated.
- Tenant ownership is represented on all repository-content records; future retrieval queries must enforce it.
- Repository contents are untrusted data, never agent instructions.

See `docs/security-checkpoint.md` for the review gate before any internet-facing integration.

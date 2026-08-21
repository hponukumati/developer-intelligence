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

## Security posture

- No secrets in source control; `.env` is ignored.
- Database and API are local-only by default.
- Repository references, URLs, request sizes, and enum values are validated.
- Tenant ownership is represented on all repository-content records; future retrieval queries must enforce it.
- Repository contents are untrusted data, never agent instructions.

See `docs/security-checkpoint.md` for the review gate before any internet-facing integration.

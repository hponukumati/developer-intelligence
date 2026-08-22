# Developer Intelligence

Local-first MVP for hybrid code search and evidence-backed pull-request reviews.

## What it does

Developer Intelligence helps you inspect code you explicitly provide to a local development instance:

- **Local code search:** paste a source file, index it, then search for relevant code chunks by keyword. With an explicit, development-only embedding-provider opt-in, it also supports semantic and hybrid retrieval.
- **Patch evidence briefs:** paste a unified diff for an indexed repository and receive the stored source chunks that overlap each changed hunk. This gives a reviewer local context without cloning a repository or sending a pull request anywhere.
- **Privacy-first defaults:** the API and database bind only to your machine. GitHub access, OAuth, webhooks, automatic comments, and deployment are not enabled.

## Current milestone

The local MVP includes a FastAPI service, PostgreSQL with pgvector, bounded local ingestion, hybrid search, and persisted evidence briefs for pasted unified diffs. GitHub OAuth, webhooks, automatic comments, and public deployment are deliberately deferred until a security-review checkpoint.

## Local development

1. Copy `.env.example` to `.env`, then set a unique local PostgreSQL password.
2. Start the API and database: `docker compose up --build`.
3. In a separate terminal: `cd apps/web && npm install && npm run dev`.
4. Browse to `http://localhost:3000`; API documentation is at `http://localhost:8000/docs`.

The Docker ports bind to loopback only. Do not add real provider or GitHub credentials until the relevant integration is implemented and reviewed.

## How to use it

### 1. Search local code

1. Open the local UI at `http://localhost:3000`.
2. Under **Ask the codebase**, enter a relative file path and paste source code.
3. Select **Index local source**. The UI creates a local repository and displays its ID.
4. Enter a question and select **Search**. The default hybrid mode remains keyword-only until embeddings are explicitly enabled and indexed.

### 2. Create a local patch evidence brief

1. Keep the repository ID from the indexing step.
2. Under **Local patch evidence**, paste that ID and a text unified diff (for example, output from `git diff`).
3. Select **Create local evidence brief**.
4. Review the returned context for each changed hunk. A “no indexed local context” message means the matching file/line range has not been indexed yet.

### 3. Optionally enable semantic search

Only do this if you accept that indexed source text and search queries will be sent to the selected embedding provider and may incur cost:

1. In **Embedding provider**, enable the toggle, enter an API key, and acknowledge the external-transfer warning.
2. Select **Create embeddings for this repository** after indexing your source.
3. Use **semantic** or **hybrid** search. Disable the toggle at any time to clear the in-memory key and stop provider calls.

## Current API flow

The current API supports a local-only code-search workflow:

1. `POST /api/repositories` with `provider: "local"` creates a repository record.
2. `POST /api/repositories/{repository_id}/documents` accepts bounded source text and a normalized relative path.
3. `POST /api/search` performs repository- and tenant-scoped keyword, semantic, or hybrid search.

After a user explicitly enables the development-only embedding provider and acknowledges the external-transfer/cost warning, `POST /api/repositories/{repository_id}/embeddings` creates vectors for the repository. Semantic search uses those vectors; hybrid search combines them with keyword candidates.

## Local patch evidence workflow

1. Index local source for a repository.
2. Paste a bounded text unified diff into `POST /api/reviews` (or the local UI).
3. The service validates diff structure and paths, stores the local review, and returns indexed source chunks that overlap each changed hunk. It explicitly reports when no local context is available.
4. `GET /api/reviews/{review_id}` reopens the stored evidence brief.

This is evidence assistance only: it does not fetch a pull request, run repository code, execute an agent, make correctness judgments, or publish comments.

The document endpoint does not access the filesystem, clone URLs, or contact GitHub. Python is chunked by top-level functions/classes; other supported text/code formats use bounded line chunks.

## Embedding provider gate

The provider interface includes a disabled adapter and an OpenAI-compatible adapter. The local UI may enable provider calls only after a user enters a key and explicitly confirms external data transfer/cost. The key is held in API process memory only (not in browser storage, `.env`, logs, database, or API responses) and is cleared when disabled or the API restarts. Runtime configuration is blocked outside `development`. With the gate on, an explicit embedding-indexing run creates vectors and semantic or hybrid search sends the query to the selected provider. With the gate off, semantic search is rejected; hybrid search stays local and truthfully reports keyword-only results.

## Hybrid retrieval foundation

`code_chunks.embedding` is a pgvector(1536) column with an HNSW cosine index. The migration is available through `docker-compose --profile tools run --rm migrate`. Keyword and vector candidates are combined with Reciprocal Rank Fusion (RRF). Vector retrieval is limited to chunks explicitly indexed after the caller enabled the development-only provider gate.

## Security posture

- No secrets in source control; `.env` is ignored.
- Database and API are local-only by default.
- Repository references, URLs, request sizes, and enum values are validated.
- Tenant ownership is represented on all repository-content records; future retrieval queries must enforce it.
- Repository contents are untrusted data, never agent instructions.
- Diff text and returned source excerpts are untrusted local display data; the service never opens paths or executes content from a patch.

See `docs/security-checkpoint.md` for the review gate before any internet-facing integration.

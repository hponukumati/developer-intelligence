# Security checkpoint before external access

Do not deploy or enable GitHub OAuth, GitHub App installation, webhooks, or review publishing until an external review covers:

1. Threat model and tenant-isolation design.
2. Authentication/session and authorization enforcement.
3. GitHub webhook signature validation, replay protection, and idempotency.
4. Secret storage, rotation, encryption, and log redaction.
5. SSRF-safe repository fetching and archive extraction limits.
6. Rate limiting, abuse controls, audit trails, and dependency scans.
7. Prompt-injection boundaries for repository content and tool outputs.
8. Data retention/deletion policy and production monitoring/alerting.

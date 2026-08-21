"""Ephemeral, development-only embedding configuration.

Secrets submitted here are deliberately held in process memory only. They are
lost on restart and never appear in API responses, logs, the database, or files.
"""
from __future__ import annotations

from threading import RLock

from app.schemas.settings import EmbeddingSettingsRead, EmbeddingSettingsUpdate
from app.retrieval.embeddings import EmbeddingProvider, build_embedding_provider


class RuntimeEmbeddingSettings:
    def __init__(self) -> None:
        self._lock = RLock()
        self._provider = "disabled"
        self._enabled = False
        self._api_key: str | None = None

    def read(self) -> EmbeddingSettingsRead:
        with self._lock:
            return EmbeddingSettingsRead(
                provider=self._provider,
                embedding_calls_enabled=self._enabled,
                api_key_configured=bool(self._api_key),
            )

    def update(self, update: EmbeddingSettingsUpdate) -> EmbeddingSettingsRead:
        with self._lock:
            if not update.embedding_calls_enabled:
                self._provider = "disabled"
                self._enabled = False
                self._api_key = None
            else:
                self._provider = update.provider
                self._enabled = True
                # get_secret_value is used only here; never include it in errors/logs/responses.
                self._api_key = update.api_key.get_secret_value() if update.api_key else None
            return self.read()

    def provider(self) -> EmbeddingProvider:
        with self._lock:
            return build_embedding_provider(self._provider, self._enabled, self._api_key or "")


runtime_embedding_settings = RuntimeEmbeddingSettings()

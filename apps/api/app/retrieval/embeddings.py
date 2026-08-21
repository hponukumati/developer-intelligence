"""Embedding-provider boundary.

Code and documentation can contain sensitive data. A provider must never be
invoked unless live embeddings are explicitly enabled in configuration.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Sequence

import httpx


class EmbeddingsDisabledError(RuntimeError):
    pass


class EmbeddingProvider(ABC):
    @abstractmethod
    def embed(self, texts: Sequence[str]) -> list[list[float]]:
        """Return one embedding per input text; implementations must preserve order."""


class DisabledEmbeddingProvider(EmbeddingProvider):
    def embed(self, texts: Sequence[str]) -> list[list[float]]:
        raise EmbeddingsDisabledError(
            "Live embeddings are disabled. Set an approved provider and enable_live_embeddings only after review."
        )


class OpenAIEmbeddingProvider(EmbeddingProvider):
    """Provider adapter. It is inert unless the factory receives explicit enablement."""

    endpoint = "https://api.openai.com/v1/embeddings"

    def __init__(self, api_key: str, model: str = "text-embedding-3-small") -> None:
        if not api_key:
            raise ValueError("OpenAI API key is required when live embeddings are enabled")
        self._api_key = api_key
        self._model = model

    def embed(self, texts: Sequence[str]) -> list[list[float]]:
        if not texts:
            return []
        # Intentionally no request/response-body logging: input may be repository source.
        response = httpx.post(
            self.endpoint,
            headers={"Authorization": f"Bearer {self._api_key}"},
            json={"model": self._model, "input": list(texts)},
            timeout=httpx.Timeout(30.0, connect=5.0),
        )
        response.raise_for_status()
        data = response.json().get("data", [])
        embeddings = [item["embedding"] for item in data]
        if len(embeddings) != len(texts):
            raise RuntimeError("Embedding provider returned an unexpected item count")
        return embeddings


def build_embedding_provider(provider: str, enable_live_embeddings: bool, openai_api_key: str) -> EmbeddingProvider:
    """Central authorization gate for outbound embedding traffic."""
    if not enable_live_embeddings or provider == "disabled":
        return DisabledEmbeddingProvider()
    if provider == "openai":
        return OpenAIEmbeddingProvider(openai_api_key)
    raise ValueError(f"Unsupported embedding provider: {provider}")

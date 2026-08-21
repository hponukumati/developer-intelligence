from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field, SecretStr, model_validator


class EmbeddingSettingsRead(BaseModel):
    provider: str
    embedding_calls_enabled: bool
    api_key_configured: bool
    storage: str = "memory_only"


class EmbeddingSettingsUpdate(BaseModel):
    provider: Literal["disabled", "openai"] = "disabled"
    embedding_calls_enabled: bool = False
    api_key: Optional[SecretStr] = Field(default=None, min_length=20, max_length=512)
    acknowledge_external_data_transfer_and_cost: bool = False

    @model_validator(mode="after")
    def validate_enablement(self):
        if self.embedding_calls_enabled:
            if self.provider != "openai":
                raise ValueError("An approved embedding provider is required when enabling calls")
            if self.api_key is None:
                raise ValueError("An API key is required when enabling embedding calls")
            if not self.acknowledge_external_data_transfer_and_cost:
                raise ValueError("Explicit acknowledgement is required before code is sent to an embedding provider")
        return self

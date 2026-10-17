"""Explicit coordinator access; the public client has no database configuration."""

from typing import Self

from pydantic import AnyHttpUrl, Field, SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class ClientSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="RELEVO_", extra="ignore", allow_inf_nan=False, hide_input_in_errors=True
    )
    api_url: AnyHttpUrl
    api_token: SecretStr = Field(min_length=32)
    http_timeout_seconds: float = Field(default=2, ge=0.001, le=60)
    submission_attempts: int = Field(default=3, ge=1, le=10)

    @model_validator(mode="after")
    def validate_origin(self) -> Self:
        if (
            self.api_url.username
            or self.api_url.password
            or self.api_url.query
            or self.api_url.fragment
            or self.api_url.path not in (None, "/")
        ):
            raise ValueError(
                "API URL must be an HTTP(S) origin without credentials, path, or query"
            )
        return self

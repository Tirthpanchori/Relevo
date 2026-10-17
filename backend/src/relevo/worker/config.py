"""Workers need coordinator access, never the engine database credentials."""

from typing import Self

from pydantic import AnyHttpUrl, Field, SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class WorkerSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="RELEVO_",
        extra="ignore",
        allow_inf_nan=False,
        hide_input_in_errors=True,
    )
    api_url: AnyHttpUrl = AnyHttpUrl("http://127.0.0.1:8000")
    api_token: SecretStr = Field(min_length=32)
    otlp_endpoint: AnyHttpUrl | None = None
    metrics_port: int = Field(default=0, ge=0, le=65_535)
    http_timeout_seconds: float = Field(default=2, ge=0.001, le=60)
    heartbeat_seconds: float = Field(default=5, ge=0.001, le=3_600)
    worker_poll_seconds: float = Field(default=0.25, ge=0.01, le=30)
    worker_monitor_seconds: float = Field(default=0.05, ge=0.001, le=1)
    worker_backoff_seconds: float = Field(default=5, ge=0.1, le=60)
    worker_report_attempts: int = Field(default=3, ge=1, le=10)

    @model_validator(mode="after")
    def validate_origin(self) -> Self:
        if self.otlp_endpoint and (
            self.otlp_endpoint.username
            or self.otlp_endpoint.password
            or self.otlp_endpoint.query
            or self.otlp_endpoint.fragment
        ):
            raise ValueError("OTLP endpoint cannot contain credentials, query, or fragment")
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

"""Validated process configuration; importing modules never connects to the database."""

from typing import Self

from pydantic import AnyHttpUrl, Field, SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine import make_url


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="RELEVO_",
        extra="ignore",
        allow_inf_nan=False,
        hide_input_in_errors=True,
    )

    database_url: SecretStr
    api_token: SecretStr = Field(min_length=32)
    otlp_endpoint: AnyHttpUrl | None = None
    metrics_port: int = Field(default=0, ge=0, le=65_535)
    lease_seconds: float = Field(default=15, ge=0.001, le=3_600)
    heartbeat_seconds: float = Field(default=5, ge=0.001, le=3_600)
    recovery_scan_seconds: float = Field(default=2, ge=0.001, le=3_600)
    recovery_batch_size: int = Field(default=100, ge=1, le=1_000)
    task_timeout_seconds: float = Field(default=60, ge=0.001, le=3_600)
    max_attempts: int = Field(default=3, ge=1, le=100)
    retry_base_seconds: float = Field(default=1, ge=0.001, le=3_600)
    retry_max_seconds: float = Field(default=30, ge=0.001, le=86_400)
    max_payload_bytes: int = Field(default=65_536, ge=1, le=65_536)
    max_result_bytes: int = Field(default=65_536, ge=1, le=65_536)
    max_request_bytes: int = Field(default=1_048_576, ge=1, le=1_048_576)
    http_timeout_seconds: float = Field(default=2, ge=0.001, le=60)
    db_connect_timeout_seconds: int = Field(default=3, ge=1, le=30)
    db_statement_timeout_ms: int = Field(default=5_000, ge=100, le=60_000)
    db_lock_timeout_ms: int = Field(default=2_000, ge=1, le=30_000)
    db_pool_size: int = Field(default=5, ge=1, le=50)

    @field_validator("database_url")
    @classmethod
    def require_postgresql(cls, value: SecretStr) -> SecretStr:
        if make_url(value.get_secret_value()).drivername != "postgresql+psycopg":
            raise ValueError("database URL must use postgresql+psycopg")
        return value

    @model_validator(mode="after")
    def validate_timing(self) -> Self:
        if self.otlp_endpoint and (
            self.otlp_endpoint.username
            or self.otlp_endpoint.password
            or self.otlp_endpoint.query
            or self.otlp_endpoint.fragment
        ):
            raise ValueError("OTLP endpoint cannot contain credentials, query, or fragment")
        if self.heartbeat_seconds + self.http_timeout_seconds >= self.lease_seconds:
            raise ValueError("heartbeat interval plus HTTP timeout must be shorter than lease")
        if self.db_lock_timeout_ms >= self.db_statement_timeout_ms:
            raise ValueError("database lock timeout must be shorter than statement timeout")
        if self.retry_base_seconds > self.retry_max_seconds:
            raise ValueError("retry base must not exceed maximum backoff")
        return self

"""Version-one contracts; public job IDs and internal attempt IDs are distinct."""

from datetime import UTC, datetime
from typing import Annotated, Literal
from uuid import UUID

from pydantic import (
    AwareDatetime,
    BaseModel,
    ConfigDict,
    Field,
    JsonValue,
    field_validator,
)

from relevo.engine.serialization import canonical_json

JobState = Literal["pending", "running", "succeeded", "failed"]
AttemptState = Literal["running", "succeeded", "failed", "expired"]
TaskType = Literal["hash_payload", "timed_work", "transient_failure"]
WorkerId = Annotated[str, Field(min_length=1, max_length=200, pattern=r"^[A-Za-z0-9_.:-]+$")]


class Contract(BaseModel):
    model_config = ConfigDict(extra="forbid", from_attributes=True, allow_inf_nan=False)


def validate_json(value: JsonValue) -> JsonValue:
    """Reject values PostgreSQL JSONB cannot represent and cap pathological nesting."""

    def visit(item: JsonValue, depth: int = 0) -> None:
        if depth > 64:
            raise ValueError("JSON nesting exceeds 64 levels")
        if isinstance(item, str):
            if "\x00" in item:
                raise ValueError("JSON strings cannot contain the null character")
            try:
                item.encode("utf-8")
            except UnicodeEncodeError as exc:
                raise ValueError("JSON strings must be valid Unicode") from exc
        elif isinstance(item, dict):
            for key, child in item.items():
                visit(key, depth + 1)
                visit(child, depth + 1)
        elif isinstance(item, list):
            for child in item:
                visit(child, depth + 1)

    visit(value)
    try:
        canonical_json(value)
    except (ValueError, OverflowError) as exc:
        raise ValueError("JSON must contain only finite numbers") from exc
    return value


class SubmitJob(Contract):
    task_type: TaskType
    payload: dict[str, JsonValue]
    run_at: AwareDatetime | None = None

    @field_validator("payload")
    @classmethod
    def valid_payload(cls, value: dict[str, JsonValue]) -> dict[str, JsonValue]:
        validate_json(value)
        return value

    @field_validator("run_at")
    @classmethod
    def normalize_schedule(cls, value: datetime | None) -> datetime | None:
        return value.astimezone(UTC) if value is not None else None


class TaskError(Contract):
    code: str = Field(min_length=1, max_length=80, pattern=r"^[a-z0-9_]+$")
    message: str = Field(min_length=1, max_length=2_000)

    @field_validator("message")
    @classmethod
    def valid_message(cls, value: str) -> str:
        validate_json(value)
        return value


class JobView(Contract):
    id: UUID
    task_type: str
    payload: dict[str, JsonValue]
    run_at: AwareDatetime | None
    state: JobState
    available_at: AwareDatetime
    created_at: AwareDatetime
    updated_at: AwareDatetime
    finished_at: AwareDatetime | None
    max_attempts: int
    attempt_count: int
    result: JsonValue = None
    error: TaskError | None = None


class AttemptView(Contract):
    id: UUID
    job_id: UUID
    number: int
    fencing_token: int
    worker_id: str
    state: AttemptState
    started_at: AwareDatetime
    lease_expires_at: AwareDatetime
    finished_at: AwareDatetime | None
    result: JsonValue = None
    error: TaskError | None = None


class AttemptHistory(Contract):
    job_id: UUID
    attempts: list[AttemptView]


class ClaimRequest(Contract):
    worker_id: WorkerId


class ClaimResponse(Contract):
    job_id: UUID
    attempt_id: UUID
    attempt_number: int
    fencing_token: int
    lease_expires_at: AwareDatetime
    task_type: TaskType
    payload: dict[str, JsonValue]
    task_timeout_seconds: float = Field(ge=0.001, le=3_600)
    lease_seconds: float = Field(ge=0.001, le=3_600)
    max_result_bytes: int = Field(ge=1, le=65_536)


class Ownership(Contract):
    worker_id: WorkerId
    fencing_token: int = Field(ge=1, le=9_223_372_036_854_775_807, strict=True)


class HeartbeatResponse(Contract):
    attempt_id: UUID
    lease_expires_at: AwareDatetime
    lease_seconds: float = Field(ge=0.001, le=3_600)


class CompleteRequest(Ownership):
    result: JsonValue

    @field_validator("result")
    @classmethod
    def valid_result(cls, value: JsonValue) -> JsonValue:
        return validate_json(value)


class FailRequest(Ownership):
    error: TaskError
    retryable: bool = Field(strict=True)


class OutcomeResponse(Contract):
    job_id: UUID
    attempt_id: UUID
    state: JobState
    available_at: AwareDatetime


class Health(Contract):
    status: Literal["ok", "ready", "not_ready"]


class ApiError(Contract):
    code: str
    message: str
    details: list[dict[str, JsonValue]] = Field(default_factory=list)


class ErrorEnvelope(Contract):
    error: ApiError

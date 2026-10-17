from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from relevo.api.schemas import SubmitJob
from relevo.config import Settings
from relevo.engine.serialization import canonical_json, fingerprint


@pytest.mark.parametrize(
    "overrides",
    [
        {"api_token": "too-short"},
        {"database_url": "sqlite:///jobs.db"},
        {"heartbeat_seconds": 14, "http_timeout_seconds": 2},
        {"lease_seconds": 0},
        {"max_attempts": 0},
        {"recovery_batch_size": 0},
        {"recovery_batch_size": 1_001},
        {"lease_seconds": float("inf")},
        {"db_lock_timeout_ms": 5_000},
        {"max_payload_bytes": 65_537},
        {"lease_seconds": 1e30},
        {"retry_base_seconds": 1e-30},
    ],
)
def test_invalid_configuration_fails_early(unit_settings: Settings, overrides: dict) -> None:
    values = unit_settings.model_dump()
    values.update(overrides)
    with pytest.raises(ValidationError):
        Settings(**values)


@pytest.mark.parametrize(
    "changes",
    [
        {"task_type": "uploaded_code"},
        {"run_at": "2026-10-16T10:00:00"},
        {"extra_field": True},
        {"payload": ["must-be-object"]},
        {"payload": {"bad": "\x00"}},
        {"payload": {"bad": "\ud800"}},
        {"payload": {"bad": float("inf")}},
        {"payload": {"bad": float("nan")}},
    ],
)
def test_invalid_requests_are_rejected(changes: dict) -> None:
    values = {"task_type": "hash_payload", "payload": {}}
    values.update(changes)
    with pytest.raises(ValidationError):
        SubmitJob.model_validate(values)


def test_request_normalization_preserves_immediate_semantics() -> None:
    first = SubmitJob(task_type="hash_payload", payload={"b": 2, "a": 1})
    second = SubmitJob(task_type="hash_payload", payload={"a": 1, "b": 2}, run_at=None)
    assert fingerprint(first.model_dump(mode="json")) == fingerprint(second.model_dump(mode="json"))
    assert first.run_at is None


def test_equivalent_timezones_have_same_fingerprint() -> None:
    first = SubmitJob.model_validate(
        {
            "task_type": "hash_payload",
            "payload": {},
            "run_at": "2026-10-16T15:30:00+05:30",
        }
    )
    second = SubmitJob.model_validate(
        {
            "task_type": "hash_payload",
            "payload": {},
            "run_at": "2026-10-16T10:00:00Z",
        }
    )
    assert first.run_at == datetime(2026, 10, 16, 10, tzinfo=UTC)
    assert fingerprint(first.model_dump(mode="json")) == fingerprint(second.model_dump(mode="json"))


def test_size_encoding_is_utf8_not_character_count() -> None:
    assert len(canonical_json({"text": "é"})) == 13


def test_json_depth_is_bounded() -> None:
    nested = {}
    for _ in range(66):
        nested = {"nested": nested}
    with pytest.raises(ValidationError):
        SubmitJob(task_type="hash_payload", payload=nested)

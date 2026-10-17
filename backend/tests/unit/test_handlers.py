import hashlib

import pytest

from relevo.engine.serialization import canonical_json
from relevo.handlers.registry import HandlerFailure, execute_handler


def test_hash_handler_uses_the_documented_canonical_bytes():
    payload = {"b": 2, "a": "é"}
    result = execute_handler("hash_payload", payload, 1)
    assert result == {
        "sha256": hashlib.sha256(canonical_json(payload)).hexdigest(),
        "bytes": len(canonical_json(payload)),
    }


def test_timed_handler_and_configured_transient_failure():
    assert execute_handler("timed_work", {"duration_seconds": 0}, 1) == {"worked_seconds": 0}
    with pytest.raises(HandlerFailure) as failure:
        execute_handler("transient_failure", {"fail_attempts": 1}, 1)
    assert failure.value.retryable
    assert execute_handler("transient_failure", {"fail_attempts": 1}, 2) == {"attempt": 2}


@pytest.mark.parametrize(
    "task,payload",
    [
        ("timed_work", {"duration_seconds": True}),
        ("timed_work", {"duration_seconds": -1}),
        ("timed_work", {"duration_seconds": float("nan")}),
        ("timed_work", {"duration_seconds": 10**500}),
        ("transient_failure", {"fail_attempts": True}),
        ("transient_failure", {"fail_attempts": 101}),
        ("arbitrary.module.function", {}),
    ],
)
def test_handlers_reject_invalid_inputs_permanently(task: str, payload: dict):
    with pytest.raises(HandlerFailure) as failure:
        execute_handler(task, payload, 1)
    assert not failure.value.retryable

"""The only executable v1 handlers; payloads never select imports or executable code."""

import hashlib
import time
from typing import Any

from relevo.engine.serialization import canonical_json


class HandlerFailure(Exception):
    def __init__(self, code: str, message: str, *, retryable: bool) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.retryable = retryable


def execute_handler(task_type: str, payload: dict[str, Any], attempt_number: int) -> Any:
    if task_type == "hash_payload":
        encoded = canonical_json(payload)
        return {"sha256": hashlib.sha256(encoded).hexdigest(), "bytes": len(encoded)}
    if task_type == "timed_work":
        duration = payload.get("duration_seconds", 1)
        if (
            isinstance(duration, bool)
            or not isinstance(duration, (int, float))
            or not 0 <= duration <= 60
        ):
            raise HandlerFailure(
                "invalid_payload",
                "duration_seconds must be a finite number from 0 to 60",
                retryable=False,
            )
        time.sleep(duration)
        return {"worked_seconds": duration}
    if task_type == "transient_failure":
        fail_attempts = payload.get("fail_attempts", 1)
        if type(fail_attempts) is not int or not 0 <= fail_attempts <= 100:
            raise HandlerFailure(
                "invalid_payload",
                "fail_attempts must be an integer from 0 to 100",
                retryable=False,
            )
        if attempt_number <= fail_attempts:
            raise HandlerFailure(
                "configured_failure",
                "Controlled transient failure",
                retryable=True,
            )
        return {"attempt": attempt_number}
    raise HandlerFailure("unknown_handler", "Task handler is not registered", retryable=False)

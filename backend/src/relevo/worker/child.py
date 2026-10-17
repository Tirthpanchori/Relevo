"""Spawn-safe, bounded file IPC. No database connection or client enters a handler process."""

import json
import multiprocessing
import os
import threading
from pathlib import Path
from time import monotonic

from relevo.engine.serialization import canonical_json
from relevo.handlers.registry import HandlerFailure, execute_handler


def execute_child(
    task_type: str,
    payload: dict,
    attempt_number: int,
    max_result_bytes: int,
    output_path: str,
    execution_deadline: float,
) -> None:
    # Spawn inherits the environment. Remove cluster credentials before invoking task code.
    for key in (
        "RELEVO_API_TOKEN",
        "RELEVO_DATABASE_URL",
        "RELEVO_TEST_DATABASE_URL",
        "POSTGRES_PASSWORD",
    ):
        os.environ.pop(key, None)
    finished = threading.Event()
    parent = multiprocessing.parent_process()

    def watch_parent() -> None:
        while not finished.wait(0.1):
            if parent is not None and not parent.is_alive():
                os._exit(70)  # Stop orphaned handler code if the supervisor dies abruptly.

    threading.Thread(target=watch_parent, name="relevo-parent-watchdog", daemon=True).start()
    started = monotonic()
    ended = None
    invoked = False
    try:
        try:
            if started >= execution_deadline:
                raise HandlerFailure(
                    "execution_timeout", "Task exceeded its execution deadline", retryable=True
                )
            invoked = True
            result = execute_handler(task_type, payload, attempt_number)
            ended = monotonic()
            if ended > execution_deadline:
                raise HandlerFailure(
                    "execution_timeout", "Task exceeded its execution deadline", retryable=True
                )
            if len(canonical_json(result)) > max_result_bytes:
                raise HandlerFailure(
                    "result_too_large", "Handler result exceeds byte limit", retryable=False
                )
            envelope = {"kind": "complete", "result": result}
        except HandlerFailure as exc:
            envelope = {
                "kind": "fail",
                "error": {"code": exc.code, "message": exc.message},
                "retryable": exc.retryable,
            }
        except Exception:
            # Handler exceptions may contain payloads/secrets. Publish a fixed diagnostic only.
            envelope = {
                "kind": "fail",
                "error": {
                    "code": "handler_error",
                    "message": "Registered handler raised an unexpected exception",
                },
                "retryable": True,
            }
        if invoked and ended is None:
            ended = monotonic()
        envelope["_handler_seconds"] = max(0, ended - started) if ended is not None else 0
        destination = Path(output_path)
        partial = destination.with_suffix(".part")
        with partial.open("xb") as stream:
            stream.write(canonical_json(envelope))
        os.replace(partial, destination)
    finally:
        finished.set()


def read_result(path: Path, max_result_bytes: int) -> dict:
    with path.open("rb") as stream:
        raw = stream.read(max_result_bytes + 16_385)
    if len(raw) > max_result_bytes + 16_384:
        raise ValueError("Handler envelope exceeds byte limit")
    return json.loads(raw)

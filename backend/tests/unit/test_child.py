"""Child execution and bounded IPC without an asyncio event loop or any sockets."""

import json
import multiprocessing
from time import monotonic

import pytest

from relevo.worker.child import execute_child, read_result


@pytest.fixture(autouse=True)
def preserve_parent_environment(monkeypatch):
    for key in (
        "RELEVO_API_TOKEN",
        "RELEVO_DATABASE_URL",
        "RELEVO_TEST_DATABASE_URL",
        "POSTGRES_PASSWORD",
    ):
        monkeypatch.setenv(key, "test-only-sentinel")


def test_real_spawned_child_writes_one_bounded_outcome(tmp_path):
    output = tmp_path / "outcome.json"
    process = multiprocessing.get_context("spawn").Process(
        target=execute_child,
        args=(
            "hash_payload",
            {"hello": "world"},
            1,
            65_536,
            str(output),
            monotonic() + 10,
        ),
    )
    try:
        process.start()
        process.join(timeout=5)
        assert not process.is_alive()
        assert process.exitcode == 0
        envelope = read_result(output, 65_536)
        assert envelope["kind"] == "complete"
        assert len(envelope["result"]["sha256"]) == 64
        assert not output.with_suffix(".part").exists()
    finally:
        if process.is_alive():
            process.terminate()
            process.join(timeout=2)
        process.close()


def test_child_rejects_oversized_output_before_ipc(tmp_path):
    output = tmp_path / "result.json"
    execute_child("hash_payload", {}, 1, 1, str(output), monotonic() + 10)
    result = json.loads(output.read_bytes())
    assert result["kind"] == "fail"
    assert result["error"]["code"] == "result_too_large" and not result["retryable"]


def test_child_does_not_start_handler_after_deadline(tmp_path):
    output = tmp_path / "expired.json"
    execute_child("timed_work", {"duration_seconds": 10}, 1, 65_536, str(output), monotonic() - 1)
    assert json.loads(output.read_bytes())["error"]["code"] == "execution_timeout"


def test_child_checks_deadline_again_after_handler_returns(tmp_path, monkeypatch):
    from relevo.worker import child

    clock = iter([0, 2])
    monkeypatch.setattr(child, "monotonic", lambda: next(clock))
    output = tmp_path / "late.json"
    execute_child("hash_payload", {}, 1, 65_536, str(output), 1)
    assert json.loads(output.read_bytes())["error"]["code"] == "execution_timeout"


def test_handler_entry_has_no_cluster_credentials(tmp_path, monkeypatch):
    import os

    from relevo.worker import child

    def check_environment(*args):
        assert all(
            key not in os.environ
            for key in (
                "RELEVO_API_TOKEN",
                "RELEVO_DATABASE_URL",
                "RELEVO_TEST_DATABASE_URL",
                "POSTGRES_PASSWORD",
            )
        )
        return {"credentials_removed": True}

    monkeypatch.setattr(child, "execute_handler", check_environment)
    output = tmp_path / "safe.json"
    execute_child("hash_payload", {}, 1, 65_536, str(output), monotonic() + 10)
    assert json.loads(output.read_bytes())["result"] == {"credentials_removed": True}

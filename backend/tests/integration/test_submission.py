from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import Engine, event, func, select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from relevo.api.schemas import SubmitJob
from relevo.config import Settings
from relevo.db.connection import database_ready, schema_head
from relevo.db.models import Job, JobEvent
from relevo.engine.errors import IdempotencyConflict, SizeLimitExceeded
from relevo.engine.jobs import submit_job

pytestmark = pytest.mark.integration


def count_rows(engine: Engine) -> tuple[int, int]:
    with Session(engine) as session:
        return (
            session.scalar(select(func.count()).select_from(Job)),
            session.scalar(select(func.count()).select_from(JobEvent)),
        )


def test_submission_commits_job_and_event_and_can_be_inspected(
    api_client: TestClient,
    db_engine: Engine,
) -> None:
    response = api_client.post(
        "/jobs",
        json={"task_type": "hash_payload", "payload": {"data": "hello"}},
        headers={"Idempotency-Key": "first-job"},
    )
    assert response.status_code == 201
    job = response.json()
    assert job["state"] == "pending"
    assert job["attempt_count"] == 0
    assert job["max_attempts"] == 3
    assert response.headers["Location"] == f"/jobs/{job['id']}"
    assert api_client.get(f"/jobs/{job['id']}").json() == job
    assert api_client.get(f"/jobs/{job['id']}/attempts").json() == {
        "job_id": job["id"],
        "attempts": [],
    }
    assert count_rows(db_engine) == (1, 1)
    with Session(db_engine) as session:
        committed_event = session.get(JobEvent, (job["id"], 1))
        assert committed_event.kind == "submitted"


def test_concurrent_duplicate_submission_is_one_job_and_one_event(
    db_engine: Engine,
    db_settings: Settings,
) -> None:
    start = Barrier(8)
    request = SubmitJob(task_type="hash_payload", payload={"a": 1})

    def submit(_: int) -> tuple:
        start.wait(timeout=10)
        job, created = submit_job(db_engine, db_settings, request, "concurrent-key")
        return job.id, created

    with ThreadPoolExecutor(max_workers=8) as pool:
        outcomes = list(pool.map(submit, range(8)))
    assert len({job_id for job_id, _ in outcomes}) == 1
    assert sum(created for _, created in outcomes) == 1
    assert count_rows(db_engine) == (1, 1)


def test_concurrent_changed_content_cannot_rebind_key(
    db_engine: Engine,
    db_settings: Settings,
) -> None:
    start = Barrier(2)

    def submit(value: int) -> str:
        start.wait(timeout=10)
        try:
            submit_job(
                db_engine,
                db_settings,
                SubmitJob(task_type="hash_payload", payload={"value": value}),
                "conflicting-key",
            )
            return "created"
        except IdempotencyConflict:
            return "conflict"

    with ThreadPoolExecutor(max_workers=2) as pool:
        outcomes = list(pool.map(submit, range(2)))
    assert sorted(outcomes) == ["conflict", "created"]
    assert count_rows(db_engine) == (1, 1)


def test_replay_normalizes_keys_and_timezone_but_conflicts_on_changed_schedule(
    api_client: TestClient,
) -> None:
    first = api_client.post(
        "/jobs",
        headers={"Idempotency-Key": "scheduled"},
        json={
            "task_type": "hash_payload",
            "payload": {"a": 1, "b": 2},
            "run_at": "2030-01-01T15:30:00+05:30",
        },
    )
    replay = api_client.post(
        "/jobs",
        headers={"Idempotency-Key": "scheduled"},
        json={
            "task_type": "hash_payload",
            "payload": {"b": 2, "a": 1},
            "run_at": "2030-01-01T10:00:00Z",
        },
    )
    assert first.status_code == 201
    assert replay.status_code == 200
    assert first.json() == replay.json()
    conflict = api_client.post(
        "/jobs",
        headers={"Idempotency-Key": "scheduled"},
        json={
            "task_type": "hash_payload",
            "payload": {"a": 1, "b": 2},
            "run_at": None,
        },
    )
    assert conflict.status_code == 409
    assert conflict.json()["error"]["code"] == "idempotency_conflict"


def test_exact_byte_boundary_and_oversized_payload(
    api_client: TestClient, db_engine: Engine
) -> None:
    # Canonical {"x":"..."} adds eight bytes. Non-ASCII input counts UTF-8 bytes.
    accepted = api_client.post(
        "/jobs",
        headers={"Idempotency-Key": "boundary"},
        json={"task_type": "hash_payload", "payload": {"x": "é" * 32_764}},
    )
    assert accepted.status_code == 201
    rejected = api_client.post(
        "/jobs",
        headers={"Idempotency-Key": "too-large"},
        json={"task_type": "hash_payload", "payload": {"x": "é" * 32_765}},
    )
    assert rejected.status_code == 413
    assert count_rows(db_engine) == (1, 1)


@pytest.mark.parametrize("suffix", ["", "/attempts"])
def test_unknown_job_is_not_found(api_client: TestClient, suffix: str) -> None:
    assert api_client.get(f"/jobs/{uuid4()}{suffix}").status_code == 404


def test_database_event_failure_rolls_back_submission(
    db_engine: Engine,
    db_settings: Settings,
) -> None:
    def fail_event(conn, cursor, statement, parameters, context, executemany):
        if statement.lstrip().startswith("INSERT INTO job_events"):
            raise RuntimeError("controlled failure before event commit")

    event.listen(db_engine, "before_cursor_execute", fail_event)
    try:
        with pytest.raises(RuntimeError, match="controlled failure"):
            submit_job(
                db_engine,
                db_settings,
                SubmitJob(task_type="hash_payload", payload={}),
                "rolled-back",
            )
    finally:
        event.remove(db_engine, "before_cursor_execute", fail_event)
    assert count_rows(db_engine) == (0, 0)


def test_failed_commit_does_not_return_success(api_client: TestClient, db_engine: Engine) -> None:
    def fail_before_commit(connection):
        raise RuntimeError("controlled commit failure")

    event.listen(db_engine, "commit", fail_before_commit)
    # Bind the test hook to the app's independently pooled engine too.
    api_engine = api_client.app.state.engine
    event.listen(api_engine, "commit", fail_before_commit)
    try:
        with pytest.raises(RuntimeError, match="commit failure"):
            api_client.post(
                "/jobs",
                json={"task_type": "hash_payload", "payload": {}},
                headers={"Idempotency-Key": "commit-failure"},
            )
    finally:
        event.remove(db_engine, "commit", fail_before_commit)
        event.remove(api_engine, "commit", fail_before_commit)
    assert count_rows(db_engine) == (0, 0)


def test_lost_submission_response_retries_original_committed_job(
    api_client: TestClient,
    db_engine: Engine,
) -> None:
    # Drop the response at the client transport boundary after the app has committed it.
    body = {"task_type": "hash_payload", "payload": {"work": "once"}}
    original_transport = api_client._transport

    class DropResponse:
        def handle_request(self, request):
            response = original_transport.handle_request(request)
            response.close()
            raise ConnectionError("controlled lost response after commit")

    api_client._transport = DropResponse()
    try:
        with pytest.raises(ConnectionError, match="lost response"):
            api_client.post("/jobs", json=body, headers={"Idempotency-Key": "lost-response"})
    finally:
        api_client._transport = original_transport
    assert count_rows(db_engine) == (1, 1)
    replay = api_client.post("/jobs", json=body, headers={"Idempotency-Key": "lost-response"})
    assert replay.status_code == 200
    with Session(db_engine) as session:
        assert str(session.scalar(select(Job.id))) == replay.json()["id"]
    assert count_rows(db_engine) == (1, 1)


def test_readiness_checks_migration_and_durability(db_engine: Engine) -> None:
    assert database_ready(db_engine, schema_head())
    assert not database_ready(db_engine, "unexpected-revision")


def test_schema_rejects_orphan_ownership(db_engine: Engine, db_settings: Settings) -> None:
    job, _ = submit_job(
        db_engine,
        db_settings,
        SubmitJob(task_type="hash_payload", payload={}),
        "orphan-owner",
    )
    with pytest.raises(IntegrityError), db_engine.begin() as connection:
        connection.execute(
            text("UPDATE jobs SET state='running', current_attempt_id=:attempt WHERE id=:id"),
            {"attempt": uuid4(), "id": job.id},
        )


def test_committed_submission_replay_survives_lower_payload_admission_limit(
    db_engine: Engine,
    db_settings: Settings,
) -> None:
    request = SubmitJob(task_type="hash_payload", payload={"message": "already accepted"})
    original, _ = submit_job(db_engine, db_settings, request, "before-limit-change")
    lower_limits = Settings(**{**db_settings.model_dump(), "max_payload_bytes": 2})
    replay, created = submit_job(db_engine, lower_limits, request, "before-limit-change")
    assert not created and replay == original
    with pytest.raises(SizeLimitExceeded):
        submit_job(db_engine, lower_limits, request, "new-after-limit-change")
    with pytest.raises(IdempotencyConflict):
        submit_job(
            db_engine,
            lower_limits,
            SubmitJob(
                task_type="hash_payload",
                payload={"different": "work"},
            ),
            "before-limit-change",
        )
    assert count_rows(db_engine) == (1, 1)

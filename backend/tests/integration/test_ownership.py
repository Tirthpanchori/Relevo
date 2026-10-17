"""Real PostgreSQL ownership proofs, synchronized at observable execution points."""

from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from threading import Barrier, Event
from time import monotonic
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import Engine, event, text
from sqlalchemy.exc import IntegrityError

from relevo.api.schemas import CompleteRequest, FailRequest, Ownership, SubmitJob, TaskError
from relevo.config import Settings
from relevo.db.connection import build_engine
from relevo.engine.errors import OwnershipConflict, SizeLimitExceeded
from relevo.engine.jobs import get_attempts, get_job, submit_job
from relevo.engine.ownership import claim_job, renew_lease, report_outcome

pytestmark = pytest.mark.integration


def create_assignment(engine: Engine, settings: Settings):
    job, _ = submit_job(
        engine,
        settings,
        SubmitJob(task_type="hash_payload", payload={"work": "test"}),
        str(uuid4()),
    )
    assignment = claim_job(engine, settings, "worker-a")
    assert assignment is not None and assignment.job_id == job.id
    return assignment


def identity(assignment) -> Ownership:
    return Ownership(worker_id="worker-a", fencing_token=assignment.fencing_token)


def completion(assignment, result=None) -> CompleteRequest:
    return CompleteRequest(**identity(assignment).model_dump(), result=result)


def failure(assignment, *, retryable=True) -> FailRequest:
    return FailRequest(
        **identity(assignment).model_dump(),
        error=TaskError(code="controlled_failure", message="Try again"),
        retryable=retryable,
    )


def expire(engine: Engine, attempt_id) -> None:
    with engine.begin() as connection:
        connection.execute(
            text("""
            UPDATE attempts SET lease_expires_at=clock_timestamp()-interval '1 second' WHERE id=:id
        """),
            {"id": attempt_id},
        )


def make_eligible(engine: Engine, job_id) -> None:
    with engine.begin() as connection:
        connection.execute(
            text("""
            UPDATE jobs SET available_at=clock_timestamp()-interval '1 second' WHERE id=:id
        """),
            {"id": job_id},
        )


def history(engine: Engine, job_id) -> list[dict]:
    with engine.connect() as connection:
        return [
            dict(row)
            for row in connection.execute(
                text("""
            SELECT sequence, kind, attempt_id, data FROM job_events
            WHERE job_id=:id ORDER BY sequence
        """),
                {"id": job_id},
            ).mappings()
        ]


def test_competing_workers_create_one_atomic_assignment(db_engine: Engine, db_settings: Settings):
    job, _ = submit_job(
        db_engine,
        db_settings,
        SubmitJob(task_type="hash_payload", payload={}),
        "one-contested-job",
    )
    start = Barrier(8)

    def claim(index):
        start.wait(timeout=10)
        return claim_job(db_engine, db_settings, f"worker-{index}")

    with ThreadPoolExecutor(max_workers=8) as pool:
        assignments = [value for value in pool.map(claim, range(8)) if value is not None]
    assert len(assignments) == 1
    assert assignments[0].attempt_number == assignments[0].fencing_token == 1
    stored = get_job(db_engine, job.id)
    assert stored.state == "running" and stored.attempt_count == 1
    assert len(get_attempts(db_engine, job.id).attempts) == 1
    assert [item["kind"] for item in history(db_engine, job.id)] == ["submitted", "claimed"]


def test_many_workers_claim_distinct_jobs(db_engine: Engine, db_settings: Settings):
    jobs = [
        submit_job(
            db_engine,
            db_settings,
            SubmitJob(task_type="hash_payload", payload={}),
            f"many-{index}",
        )[0]
        for index in range(20)
    ]
    start = Barrier(8)

    def drain(index):
        start.wait(timeout=10)
        assignments = []
        while (assignment := claim_job(db_engine, db_settings, f"worker-{index}")) is not None:
            assignments.append(assignment)
        return assignments

    with ThreadPoolExecutor(max_workers=8) as pool:
        assignments = [assignment for group in pool.map(drain, range(8)) for assignment in group]
    assert {assignment.job_id for assignment in assignments} == {job.id for job in jobs}
    assert len({assignment.attempt_id for assignment in assignments}) == len(jobs)


def test_locked_candidate_is_skipped(db_engine: Engine, db_settings: Settings):
    first, _ = submit_job(
        db_engine,
        db_settings,
        SubmitJob(task_type="hash_payload", payload={}),
        "locked-first",
    )
    second, _ = submit_job(
        db_engine,
        db_settings,
        SubmitJob(task_type="hash_payload", payload={}),
        "unlocked-second",
    )
    with db_engine.begin() as blocker:
        blocker.execute(text("SELECT id FROM jobs WHERE id=:id FOR UPDATE"), {"id": first.id})
        claimed = claim_job(db_engine, db_settings, "worker-a")
        assert claimed.job_id == second.id
    assert claim_job(db_engine, db_settings, "worker-b").job_id == first.id


def test_future_job_is_not_claimed_and_no_work_has_empty_http_response(
    api_client: TestClient,
    db_engine: Engine,
    db_settings: Settings,
):
    with db_engine.connect() as connection:
        now = connection.execute(text("SELECT clock_timestamp()")).scalar_one()
    job, _ = submit_job(
        db_engine,
        db_settings,
        SubmitJob(
            task_type="hash_payload",
            payload={},
            run_at=now + timedelta(minutes=5),
        ),
        "future",
    )
    response = api_client.post("/internal/claim", json={"worker_id": "worker-a"})
    assert response.status_code == 204 and response.content == b""
    assert get_job(db_engine, job.id).state == "pending"
    make_eligible(db_engine, job.id)
    assert claim_job(db_engine, db_settings, "worker-a").job_id == job.id


def test_claim_rollback_preserves_pending_job(db_engine: Engine, db_settings: Settings):
    job, _ = submit_job(
        db_engine,
        db_settings,
        SubmitJob(task_type="hash_payload", payload={}),
        "rollback-claim",
    )

    def fail_event(conn, cursor, statement, parameters, context, executemany):
        if statement.lstrip().startswith("INSERT INTO job_events"):
            raise RuntimeError("controlled claim event failure")

    event.listen(db_engine, "before_cursor_execute", fail_event)
    try:
        with pytest.raises(RuntimeError, match="claim event failure"):
            claim_job(db_engine, db_settings, "worker-a")
    finally:
        event.remove(db_engine, "before_cursor_execute", fail_event)
    stored = get_job(db_engine, job.id)
    assert stored.state == "pending" and stored.attempt_count == 0
    assert get_attempts(db_engine, job.id).attempts == []
    assert len(history(db_engine, job.id)) == 1


def test_heartbeat_extends_lease_without_extra_state_transition(
    db_engine: Engine, db_settings: Settings
):
    assignment = create_assignment(db_engine, db_settings)
    renewed = renew_lease(db_engine, db_settings, assignment.attempt_id, identity(assignment))
    assert renewed.lease_expires_at > assignment.lease_expires_at
    assert len(history(db_engine, assignment.job_id)) == 2


def test_renewal_does_not_shorten_a_lease_after_configuration_change(
    db_engine: Engine,
    db_settings: Settings,
):
    assignment = create_assignment(db_engine, db_settings)
    shorter = Settings(
        **{
            **db_settings.model_dump(),
            "lease_seconds": 6,
            "heartbeat_seconds": 1,
        }
    )
    renewed = renew_lease(db_engine, shorter, assignment.attempt_id, identity(assignment))
    assert renewed.lease_expires_at == assignment.lease_expires_at


def test_claim_order_uses_uuid_to_break_equal_time_ties(db_engine: Engine, db_settings: Settings):
    jobs = [
        submit_job(
            db_engine,
            db_settings,
            SubmitJob(task_type="hash_payload", payload={}),
            f"tied-{number}",
        )[0]
        for number in range(3)
    ]
    with db_engine.begin() as connection:
        connection.execute(
            text("""
            UPDATE jobs SET available_at='2020-01-01T00:00:00Z', created_at='2020-01-01T00:00:00Z'
        """)
        )
    claimed_ids = [claim_job(db_engine, db_settings, "worker-a").job_id for _ in range(3)]
    assert claimed_ids == sorted(job.id for job in jobs)


@pytest.mark.parametrize("operation", ["heartbeat", "complete", "fail"])
def test_final_sql_guard_rejects_expiry_after_initial_ownership_check(
    db_engine: Engine,
    db_settings: Settings,
    operation: str,
):
    assignment = create_assignment(db_engine, db_settings)

    def expire_before_guard(connection, cursor, statement, parameters, context, executemany):
        if (
            "UPDATE attempts SET" in statement
            and "lease_expires_at > clock_timestamp()" in statement
        ):
            # Move the controlled deadline at the last write boundary, after the initial check.
            connection.execute(
                text("""
                UPDATE attempts SET lease_expires_at=clock_timestamp() WHERE id=:id
            """),
                {"id": assignment.attempt_id},
            )

    event.listen(db_engine, "before_cursor_execute", expire_before_guard)
    try:
        with pytest.raises(OwnershipConflict, match="expired before"):
            if operation == "heartbeat":
                renew_lease(db_engine, db_settings, assignment.attempt_id, identity(assignment))
            else:
                report_outcome(
                    db_engine,
                    db_settings,
                    assignment.attempt_id,
                    completion(assignment) if operation == "complete" else failure(assignment),
                )
    finally:
        event.remove(db_engine, "before_cursor_execute", expire_before_guard)
    assert get_job(db_engine, assignment.job_id).state == "running"
    assert len(history(db_engine, assignment.job_id)) == 2


@pytest.mark.parametrize("operation", ["heartbeat", "complete", "fail"])
@pytest.mark.parametrize("wrong", [{"worker_id": "impostor"}, {"fencing_token": 99}])
def test_wrong_identity_cannot_mutate_ownership(
    db_engine: Engine,
    db_settings: Settings,
    operation: str,
    wrong: dict,
):
    assignment = create_assignment(db_engine, db_settings)
    values = {**identity(assignment).model_dump(), **wrong}
    with pytest.raises(OwnershipConflict):
        if operation == "heartbeat":
            renew_lease(db_engine, db_settings, assignment.attempt_id, Ownership(**values))
        else:
            report = (
                CompleteRequest(**values, result=None)
                if operation == "complete"
                else FailRequest(
                    **values, error=TaskError(code="wrong", message="wrong"), retryable=False
                )
            )
            report_outcome(db_engine, db_settings, assignment.attempt_id, report)
    assert get_job(db_engine, assignment.job_id).state == "running"
    assert len(history(db_engine, assignment.job_id)) == 2


@pytest.mark.parametrize("operation", ["heartbeat", "complete", "fail"])
def test_expired_lease_rejected_without_waiting_for_recovery(
    db_engine: Engine,
    db_settings: Settings,
    operation: str,
):
    assignment = create_assignment(db_engine, db_settings)
    expire(db_engine, assignment.attempt_id)
    with pytest.raises(OwnershipConflict):
        if operation == "heartbeat":
            renew_lease(db_engine, db_settings, assignment.attempt_id, identity(assignment))
        else:
            report_outcome(
                db_engine,
                db_settings,
                assignment.attempt_id,
                completion(assignment) if operation == "complete" else failure(assignment),
            )
    assert get_job(db_engine, assignment.job_id).state == "running"
    assert len(history(db_engine, assignment.job_id)) == 2


def test_completion_and_identical_replay_are_durable(db_engine: Engine, db_settings: Settings):
    assignment = create_assignment(db_engine, db_settings)
    report = completion(assignment, {"a": 1, "b": 2})
    outcome = report_outcome(db_engine, db_settings, assignment.attempt_id, report)
    expire(db_engine, assignment.attempt_id)
    replay = report_outcome(
        db_engine, db_settings, assignment.attempt_id, completion(assignment, {"b": 2, "a": 1})
    )
    assert replay == outcome and outcome.state == "succeeded"
    lower_limits = Settings(**{**db_settings.model_dump(), "max_result_bytes": 1})
    assert report_outcome(db_engine, lower_limits, assignment.attempt_id, report) == outcome
    with pytest.raises(OwnershipConflict):
        report_outcome(
            db_engine,
            db_settings,
            assignment.attempt_id,
            CompleteRequest(
                worker_id="wrong-worker",
                fencing_token=assignment.fencing_token,
                result=report.result,
            ),
        )
    stored = get_job(db_engine, assignment.job_id)
    attempt = get_attempts(db_engine, assignment.job_id).attempts[0]
    assert stored.result == attempt.result == {"a": 1, "b": 2}
    assert stored.error is None and stored.finished_at == attempt.finished_at
    assert [item["kind"] for item in history(db_engine, assignment.job_id)] == [
        "submitted",
        "claimed",
        "succeeded",
    ]
    with pytest.raises(OwnershipConflict):
        report_outcome(
            db_engine, db_settings, assignment.attempt_id, completion(assignment, "different")
        )
    with pytest.raises(OwnershipConflict):
        report_outcome(db_engine, db_settings, assignment.attempt_id, failure(assignment))
    with pytest.raises(OwnershipConflict):
        renew_lease(db_engine, db_settings, assignment.attempt_id, identity(assignment))


def test_retry_reassignment_fences_old_owner_and_accepts_historical_report(
    db_engine: Engine,
    db_settings: Settings,
):
    first = create_assignment(db_engine, db_settings)
    old_report = failure(first)
    original = report_outcome(
        db_engine, db_settings, first.attempt_id, old_report, random_source=lambda: 1
    )
    assert original.state == "pending"
    assert claim_job(db_engine, db_settings, "worker-b") is None
    make_eligible(db_engine, first.job_id)
    second = claim_job(db_engine, db_settings, "worker-b")
    assert second.attempt_number == second.fencing_token == 2
    replay = report_outcome(db_engine, db_settings, first.attempt_id, old_report)
    assert replay == original  # Original historical acknowledgment, not the current job state.
    assert get_job(db_engine, first.job_id).state == "running"
    assert len(history(db_engine, first.job_id)) == 4
    with pytest.raises(OwnershipConflict):
        report_outcome(db_engine, db_settings, first.attempt_id, completion(first))
    with pytest.raises(OwnershipConflict):
        renew_lease(db_engine, db_settings, first.attempt_id, identity(first))
    report_outcome(
        db_engine,
        db_settings,
        second.attempt_id,
        CompleteRequest(
            worker_id="worker-b",
            fencing_token=second.fencing_token,
            result="done",
        ),
    )
    assert report_outcome(db_engine, db_settings, first.attempt_id, old_report) == original
    assert get_job(db_engine, first.job_id).state == "succeeded"
    assert len(history(db_engine, first.job_id)) == 5


def test_retry_budget_counts_total_attempts(db_engine: Engine, db_settings: Settings):
    assignment = create_assignment(db_engine, db_settings)
    for number in range(1, 4):
        outcome = report_outcome(db_engine, db_settings, assignment.attempt_id, failure(assignment))
        assert outcome.state == ("pending" if number < 3 else "failed")
        if number < 3:
            make_eligible(db_engine, assignment.job_id)
            assignment = claim_job(db_engine, db_settings, "worker-a")
            assert assignment.attempt_number == number + 1
    assert claim_job(db_engine, db_settings, "worker-a") is None
    assert len(get_attempts(db_engine, assignment.job_id).attempts) == 3
    assert len(history(db_engine, assignment.job_id)) == 7


def test_permanent_failure_does_not_retry(db_engine: Engine, db_settings: Settings):
    assignment = create_assignment(db_engine, db_settings)
    outcome = report_outcome(
        db_engine, db_settings, assignment.attempt_id, failure(assignment, retryable=False)
    )
    assert outcome.state == "failed"
    assert get_job(db_engine, assignment.job_id).attempt_count == 1
    assert claim_job(db_engine, db_settings, "worker-b") is None


def test_result_byte_limit_does_not_consume_valid_ownership(
    db_engine: Engine, db_settings: Settings
):
    assignment = create_assignment(db_engine, db_settings)
    with pytest.raises(SizeLimitExceeded):
        report_outcome(
            db_engine, db_settings, assignment.attempt_id, completion(assignment, "é" * 32_768)
        )
    assert get_job(db_engine, assignment.job_id).state == "running"
    assert len(history(db_engine, assignment.job_id)) == 2
    outcome = report_outcome(
        db_engine, db_settings, assignment.attempt_id, completion(assignment, "é" * 32_767)
    )
    assert outcome.state == "succeeded"


def test_competing_complete_and_fail_have_one_winner(db_engine: Engine, db_settings: Settings):
    assignment = create_assignment(db_engine, db_settings)
    start = Barrier(2)

    def report(body):
        start.wait(timeout=10)
        try:
            return report_outcome(db_engine, db_settings, assignment.attempt_id, body).state
        except OwnershipConflict:
            return "conflict"

    with ThreadPoolExecutor(max_workers=2) as pool:
        outcomes = list(
            pool.map(report, [completion(assignment), failure(assignment, retryable=False)])
        )
    assert outcomes.count("conflict") == 1
    assert get_job(db_engine, assignment.job_id).state in outcomes
    assert len(history(db_engine, assignment.job_id)) == 3


def test_competing_heartbeat_and_completion_serialize_without_reopening_terminal_job(
    db_engine: Engine,
    db_settings: Settings,
):
    assignment = create_assignment(db_engine, db_settings)
    start = Barrier(2)

    def run(operation):
        start.wait(timeout=10)
        if operation == "complete":
            return report_outcome(
                db_engine, db_settings, assignment.attempt_id, completion(assignment)
            ).state
        try:
            renew_lease(db_engine, db_settings, assignment.attempt_id, identity(assignment))
            return "renewed"
        except OwnershipConflict:
            return "conflict"

    with ThreadPoolExecutor(max_workers=2) as pool:
        complete, heartbeat = list(pool.map(run, ["complete", "heartbeat"]))
    assert complete == "succeeded" and heartbeat in ("renewed", "conflict")
    assert get_job(db_engine, assignment.job_id).state == "succeeded"
    assert get_attempts(db_engine, assignment.job_id).attempts[0].state == "succeeded"
    assert len(history(db_engine, assignment.job_id)) == 3


@pytest.mark.parametrize("kind", ["complete", "fail"])
def test_concurrent_identical_reports_add_one_transition(
    db_engine: Engine,
    db_settings: Settings,
    kind: str,
):
    assignment = create_assignment(db_engine, db_settings)
    body = completion(assignment) if kind == "complete" else failure(assignment)
    start = Barrier(4)

    def report(_):
        start.wait(timeout=10)
        return report_outcome(db_engine, db_settings, assignment.attempt_id, body)

    with ThreadPoolExecutor(max_workers=4) as pool:
        outcomes = list(pool.map(report, range(4)))
    assert all(outcome == outcomes[0] for outcome in outcomes)
    assert len(history(db_engine, assignment.job_id)) == 3


def test_outcome_event_failure_rolls_back_both_state_changes(
    db_engine: Engine, db_settings: Settings
):
    assignment = create_assignment(db_engine, db_settings)

    def fail_event(conn, cursor, statement, parameters, context, executemany):
        if statement.lstrip().startswith("INSERT INTO job_events"):
            raise RuntimeError("controlled outcome event failure")

    event.listen(db_engine, "before_cursor_execute", fail_event)
    try:
        with pytest.raises(RuntimeError, match="outcome event failure"):
            report_outcome(db_engine, db_settings, assignment.attempt_id, completion(assignment))
    finally:
        event.remove(db_engine, "before_cursor_execute", fail_event)
    assert get_job(db_engine, assignment.job_id).state == "running"
    assert get_attempts(db_engine, assignment.job_id).attempts[0].state == "running"
    assert len(history(db_engine, assignment.job_id)) == 2


def test_database_prevents_second_running_attempt(db_engine: Engine, db_settings: Settings):
    assignment = create_assignment(db_engine, db_settings)
    with pytest.raises(IntegrityError), db_engine.begin() as connection:
        connection.execute(
            text("""
            INSERT INTO attempts
                (id, job_id, number, fencing_token, worker_id, state, started_at, lease_expires_at)
            SELECT :id, job_id, 2, 2, 'worker-b', 'running', started_at, lease_expires_at
            FROM attempts WHERE id=:original
        """),
            {"id": uuid4(), "original": assignment.attempt_id},
        )
    assert len(get_attempts(db_engine, assignment.job_id).attempts) == 1


@pytest.mark.parametrize("operation", ["heartbeat", "complete", "fail"])
def test_lock_wait_cannot_use_transaction_start_to_resurrect_expired_lease(
    db_engine: Engine,
    db_settings: Settings,
    operation: str,
):
    assignment = create_assignment(db_engine, db_settings)
    waiting_engine = build_engine(
        Settings(
            **{
                **db_settings.model_dump(),
                "db_lock_timeout_ms": 10_000,
                "db_statement_timeout_ms": 15_000,
            }
        )
    )
    waiting = Event()
    waiter_pid = []

    def about_to_lock(connection, cursor, statement, parameters, context, executemany):
        if "FROM jobs WHERE id=" in statement and "FOR UPDATE" in statement:
            waiter_pid.append(connection.connection.driver_connection.info.backend_pid)
            waiting.set()

    event.listen(waiting_engine, "before_cursor_execute", about_to_lock)

    def report_or_renew():
        if operation == "heartbeat":
            return renew_lease(
                waiting_engine, db_settings, assignment.attempt_id, identity(assignment)
            )
        return report_outcome(
            waiting_engine,
            db_settings,
            assignment.attempt_id,
            completion(assignment) if operation == "complete" else failure(assignment),
        )

    try:
        with ThreadPoolExecutor(max_workers=1) as pool:
            with db_engine.begin() as blocker:
                blocker.execute(
                    text("SELECT id FROM jobs WHERE id=:id FOR UPDATE"), {"id": assignment.job_id}
                )
                future = pool.submit(report_or_renew)
                assert waiting.wait(timeout=5)
                # Wait for observable database lock contention, not an arbitrary race-test sleep.
                deadline = monotonic() + 5
                with db_engine.connect() as observer:
                    while True:
                        activity = observer.execute(
                            text("""
                            SELECT wait_event_type, xact_start FROM pg_stat_activity WHERE pid=:pid
                        """),
                            {"pid": waiter_pid[0]},
                        ).one()
                        if activity.wait_event_type == "Lock":
                            break
                        assert monotonic() < deadline, (
                            "ownership call did not block on the job lock"
                        )
                        observer.rollback()  # Release the statistics snapshot before the next poll.
                        Event().wait(0.005)
                expiry = blocker.execute(
                    text("""
                    UPDATE attempts SET lease_expires_at=clock_timestamp() WHERE id=:id
                    RETURNING lease_expires_at
                """),
                    {"id": assignment.attempt_id},
                ).scalar_one()
                assert activity.xact_start < expiry
            with pytest.raises(OwnershipConflict):
                future.result(timeout=10)
        assert get_job(db_engine, assignment.job_id).state == "running"
        assert len(history(db_engine, assignment.job_id)) == 2
    finally:
        event.remove(waiting_engine, "before_cursor_execute", about_to_lock)
        waiting_engine.dispose()

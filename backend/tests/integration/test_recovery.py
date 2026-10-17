"""Real PostgreSQL expiry, transaction, overlapping-scan, and restart evidence."""

import os
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier, Event
from time import monotonic

import pytest
from sqlalchemy import Engine, event, text

from relevo.api.schemas import SubmitJob
from relevo.config import Settings
from relevo.db.connection import build_engine
from relevo.engine.errors import OwnershipConflict
from relevo.engine.jobs import get_attempts, get_job, submit_job
from relevo.engine.ownership import claim_job, renew_lease, report_outcome
from relevo.engine.recovery import recover_expired
from tests.integration.test_ownership import (
    completion,
    create_assignment,
    expire,
    history,
    identity,
    make_eligible,
)

pytestmark = pytest.mark.integration


def test_live_lease_is_not_recovered(db_engine: Engine, db_settings: Settings):
    assigned = create_assignment(db_engine, db_settings)
    renew_lease(db_engine, db_settings, assigned.attempt_id, identity(assigned))
    assert recover_expired(db_engine, db_settings) == []
    assert get_job(db_engine, assigned.job_id).state == "running"
    assert (
        report_outcome(db_engine, db_settings, assigned.attempt_id, completion(assigned)).state
        == "succeeded"
    )
    assert recover_expired(db_engine, db_settings) == []


def test_expiry_delays_retry_and_fences_old_owner(db_engine: Engine, db_settings: Settings):
    assigned = create_assignment(db_engine, db_settings)
    expire(db_engine, assigned.attempt_id)
    recovered = recover_expired(db_engine, db_settings, random_source=lambda: 0)
    assert len(recovered) == 1 and recovered[0].state == "pending"
    stored = get_job(db_engine, assigned.job_id)
    assert stored.attempt_count == 1 and stored.state == "pending"
    assert (stored.available_at - stored.updated_at).total_seconds() == 0.5
    assert claim_job(db_engine, db_settings, "replacement") is None
    attempts = get_attempts(db_engine, assigned.job_id).attempts
    assert attempts[0].state == "expired" and attempts[0].error.code == "lease_expired"
    assert recover_expired(db_engine, db_settings) == []
    assert [row["kind"] for row in history(db_engine, assigned.job_id)] == [
        "submitted",
        "claimed",
        "expired",
    ]
    make_eligible(db_engine, assigned.job_id)
    replacement = claim_job(db_engine, db_settings, "replacement")
    assert replacement.attempt_number == 2 and replacement.fencing_token == 2
    with pytest.raises(OwnershipConflict):
        report_outcome(db_engine, db_settings, assigned.attempt_id, completion(assigned))
    with pytest.raises(OwnershipConflict):
        renew_lease(db_engine, db_settings, assigned.attempt_id, identity(assigned))


def test_expiry_budget_is_terminal_and_does_not_block_healthy_jobs(
    db_engine: Engine, db_settings: Settings
):
    settings = Settings(**{**db_settings.model_dump(), "max_attempts": 2})
    assigned = create_assignment(db_engine, settings)
    for number in (1, 2):
        expire(db_engine, assigned.attempt_id)
        outcome = recover_expired(db_engine, settings)
        assert outcome[0].state == ("pending" if number == 1 else "failed")
        if number == 1:
            make_eligible(db_engine, assigned.job_id)
            assigned = claim_job(db_engine, settings, "worker-a")
    stored = get_job(db_engine, assigned.job_id)
    assert stored.state == "failed" and stored.attempt_count == 2
    assert stored.error.code == "lease_expired"
    assert [a.state for a in get_attempts(db_engine, assigned.job_id).attempts] == [
        "expired",
        "expired",
    ]
    assert recover_expired(db_engine, settings) == []
    assert claim_job(db_engine, settings, "worker-a") is None
    healthy, _ = submit_job(
        db_engine, settings, SubmitJob(task_type="hash_payload", payload={}), "healthy-after-poison"
    )
    assert claim_job(db_engine, settings, "worker-a").job_id == healthy.id


def test_recovery_batches_are_bounded(db_engine: Engine, db_settings: Settings):
    settings = Settings(**{**db_settings.model_dump(), "recovery_batch_size": 2})
    assigned = [create_assignment(db_engine, settings) for _ in range(5)]
    for item in assigned:
        expire(db_engine, item.attempt_id)
    batches = [recover_expired(db_engine, settings) for _ in range(4)]
    assert [len(batch) for batch in batches] == [2, 2, 1, 0]
    assert {row.attempt_id for batch in batches for row in batch} == {
        item.attempt_id for item in assigned
    }


def test_overlapping_scans_close_each_expiry_once(db_engine: Engine, db_settings: Settings):
    assigned = [create_assignment(db_engine, db_settings) for _ in range(15)]
    for item in assigned:
        expire(db_engine, item.attempt_id)
    start = Barrier(6)

    def scan(_):
        start.wait(timeout=10)
        return recover_expired(db_engine, db_settings)

    with ThreadPoolExecutor(max_workers=6) as pool:
        recovered = [row for batch in pool.map(scan, range(6)) for row in batch]
    assert len(recovered) == len(assigned)
    assert len({row.attempt_id for row in recovered}) == len(assigned)
    for item in assigned:
        rows = history(db_engine, item.job_id)
        assert [row["sequence"] for row in rows] == [1, 2, 3]
        assert rows[-1]["kind"] == "expired"
        assert get_job(db_engine, item.job_id).state == "pending"


def test_locked_jobs_are_skipped_not_waited_on(db_engine: Engine, db_settings: Settings):
    first = create_assignment(db_engine, db_settings)
    second = create_assignment(db_engine, db_settings)
    expire(db_engine, first.attempt_id)
    expire(db_engine, second.attempt_id)
    with db_engine.begin() as blocker:
        blocker.execute(text("SELECT id FROM jobs WHERE id=:id FOR UPDATE"), {"id": first.job_id})
        recovered = recover_expired(db_engine, db_settings)
        assert [row.job_id for row in recovered] == [second.job_id]
    assert [row.job_id for row in recover_expired(db_engine, db_settings)] == [first.job_id]


@pytest.mark.parametrize("boundary", ["event", "commit"])
def test_interrupted_scan_rolls_back_attempt_job_and_history(
    db_engine: Engine, db_settings: Settings, boundary
):
    assigned = create_assignment(db_engine, db_settings)
    expire(db_engine, assigned.attempt_id)

    def fail_event(conn, cursor, statement, parameters, context, executemany):
        if statement.lstrip().startswith("INSERT INTO job_events"):
            raise RuntimeError("controlled scan failure")

    def fail_commit(conn):
        raise RuntimeError("controlled scan failure")

    event_name = "before_cursor_execute" if boundary == "event" else "commit"
    callback = fail_event if boundary == "event" else fail_commit
    event.listen(db_engine, event_name, callback)
    try:
        with pytest.raises(RuntimeError, match="controlled scan failure"):
            recover_expired(db_engine, db_settings)
    finally:
        event.remove(db_engine, event_name, callback)
    assert get_job(db_engine, assigned.job_id).state == "running"
    assert get_attempts(db_engine, assigned.job_id).attempts[0].state == "running"
    assert len(history(db_engine, assigned.job_id)) == 2
    assert len(recover_expired(db_engine, db_settings)) == 1


@pytest.mark.parametrize("operation", ["heartbeat", "complete"])
def test_recovery_races_with_late_owner_without_resurrection(
    db_engine: Engine, db_settings: Settings, operation
):
    assigned = create_assignment(db_engine, db_settings)
    expire(db_engine, assigned.attempt_id)
    start = Barrier(2)

    def owner():
        start.wait(timeout=10)
        with pytest.raises(OwnershipConflict):
            if operation == "heartbeat":
                renew_lease(db_engine, db_settings, assigned.attempt_id, identity(assigned))
            else:
                report_outcome(db_engine, db_settings, assigned.attempt_id, completion(assigned))

    def recovery():
        start.wait(timeout=10)
        return recover_expired(db_engine, db_settings)

    with ThreadPoolExecutor(max_workers=2) as pool:
        owner_future = pool.submit(owner)
        recovered = pool.submit(recovery).result(timeout=10)
        owner_future.result(timeout=10)
    assert len(recovered) == 1
    assert get_job(db_engine, assigned.job_id).state == "pending"
    assert len(history(db_engine, assigned.job_id)) == 3


def test_scan_revalidates_after_attempt_lock_wait(db_engine: Engine, db_settings: Settings):
    assigned = create_assignment(db_engine, db_settings)
    expire(db_engine, assigned.attempt_id)
    waiting_engine = build_engine(
        Settings(
            **{
                **db_settings.model_dump(),
                "db_lock_timeout_ms": 10_000,
                "db_statement_timeout_ms": 15_000,
            }
        )
    )
    reached = Event()
    backend_pid = []

    def on_attempt_lock(conn, cursor, statement, parameters, context, executemany):
        if "SELECT * FROM attempts WHERE" in statement:
            backend_pid.append(conn.connection.driver_connection.info.backend_pid)
            reached.set()

    event.listen(waiting_engine, "before_cursor_execute", on_attempt_lock)
    try:
        with ThreadPoolExecutor(max_workers=1) as pool:
            with db_engine.begin() as blocker:
                # Direct SQL isolates post-lock revalidation; real writers lock the job first.
                blocker.execute(
                    text("SELECT id FROM attempts WHERE id=:id FOR UPDATE"),
                    {"id": assigned.attempt_id},
                )
                future = pool.submit(recover_expired, waiting_engine, db_settings)
                assert reached.wait(timeout=5)
                deadline = monotonic() + 5
                with db_engine.connect() as observer:
                    while True:
                        waiting = observer.execute(
                            text("SELECT wait_event_type FROM pg_stat_activity WHERE pid=:pid"),
                            {"pid": backend_pid[0]},
                        ).scalar_one()
                        if waiting == "Lock":
                            break
                        assert monotonic() < deadline, "scan did not wait for the attempt lock"
                        observer.rollback()
                        Event().wait(0.005)
                blocker.execute(
                    text(
                        "UPDATE attempts SET lease_expires_at=clock_timestamp()+interval '1 hour' "
                        "WHERE id=:id"
                    ),
                    {"id": assigned.attempt_id},
                )
            assert future.result(timeout=10) == []
    finally:
        event.remove(waiting_engine, "before_cursor_execute", on_attempt_lock)
        waiting_engine.dispose()
    assert get_job(db_engine, assigned.job_id).state == "running"
    assert len(history(db_engine, assigned.job_id)) == 2


def test_new_scheduler_process_recovers_work_accumulated_while_stopped(
    db_engine: Engine, db_settings: Settings
):
    env = {
        **os.environ,
        "RELEVO_DATABASE_URL": db_settings.database_url.get_secret_value(),
        "RELEVO_API_TOKEN": db_settings.api_token.get_secret_value(),
    }
    # Each invocation has a fresh interpreter/engine and no in-memory scan cursor.
    for _ in range(2):
        assigned = create_assignment(db_engine, db_settings)
        expire(db_engine, assigned.attempt_id)
        assert get_job(db_engine, assigned.job_id).state == "running"
        process = subprocess.run(
            [sys.executable, "-m", "relevo.scheduler", "--once"],
            env=env,
            capture_output=True,
            text=True,
            timeout=15,
            check=True,
        )
        assert "Recovered expiry:" in process.stderr
        assert get_job(db_engine, assigned.job_id).state == "pending"
        assert len(history(db_engine, assigned.job_id)) == 3
        # Keep this pending retry out of the next test assignment's claim queue.
        with db_engine.begin() as connection:
            connection.execute(
                text(
                    "UPDATE jobs SET available_at=clock_timestamp()+interval '1 hour' WHERE id=:id"
                ),
                {"id": assigned.job_id},
            )

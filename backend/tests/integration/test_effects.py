"""Instrumented handler/business transactions; registered worker credentials stay unchanged."""

import asyncio
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import Barrier
from uuid import uuid4

import httpx
import pytest
from sqlalchemy import Engine, event, text

from relevo.api.schemas import CompleteRequest
from relevo.config import Settings
from relevo.demo.effects import BusinessConflict, commit_effect
from relevo.demo.recordings import capture_job, write_capture
from relevo.engine.errors import OwnershipConflict
from relevo.engine.jobs import get_attempts, get_job
from relevo.engine.ownership import claim_job, report_outcome
from relevo.engine.recovery import recover_expired
from relevo.handlers.registry import execute_handler
from relevo.worker.config import WorkerSettings
from relevo.worker.coordinator import CoordinatorClient
from relevo.worker.runtime import Worker
from tests.integration.test_ownership import create_assignment, expire, history, make_eligible

pytestmark = pytest.mark.integration


def effect_count(engine):
    with engine.connect() as connection:
        return connection.execute(text("SELECT count(*) FROM relevo_demo.effects")).scalar_one()


@pytest.mark.parametrize("protected", [False, True], ids=["unprotected", "protected"])
def test_committed_business_effect_survives_lost_completion_and_repeated_execution(
    db_engine: Engine, db_settings: Settings, protected, request
):
    assigned = create_assignment(db_engine, db_settings)
    key = f"business-{uuid4()}"
    observations = []

    def execute(assignment):
        # This harness augments the real hashing handler with a separate business transaction.
        result = execute_handler(
            assignment.task_type, assignment.payload, assignment.attempt_number
        )
        effect = commit_effect(
            db_engine,
            business_key=key,
            units=1,
            job_id=assignment.job_id,
            attempt_id=assignment.attempt_id,
            protected=protected,
        )
        observations.append(
            {
                "checkpoint": "business_commit_acknowledged",
                "attempt_id": str(assignment.attempt_id),
                "effect_id": effect["effect_id"],
                "effect_count": effect_count(db_engine),
            }
        )
        return result, effect

    first_result, first_effect = execute(assigned)
    reports = []

    def disconnected(request):
        reports.append(request.content)
        raise httpx.ReadTimeout("Controlled outage before completion reaches the coordinator")

    async def lose_completion():
        settings = WorkerSettings(api_token=db_settings.api_token)
        async with CoordinatorClient(
            settings, transport=httpx.MockTransport(disconnected)
        ) as client:
            worker = Worker(client, settings, worker_id="worker-a")
            assert (
                await worker.deliver(assigned, {"kind": "complete", "result": first_result})
                == "unavailable"
            )

    asyncio.run(lose_completion())
    assert len(reports) == 3 and len(set(reports)) == 1
    assert get_job(db_engine, assigned.job_id).state == "running" and effect_count(db_engine) == 1
    observations.append({"checkpoint": "all_three_completion_requests_dropped_before_coordinator"})
    expire(db_engine, assigned.attempt_id)
    observations.append({"checkpoint": "lease_forced_expired_by_test_sql"})
    assert len(recover_expired(db_engine, db_settings)) == 1
    make_eligible(db_engine, assigned.job_id)
    replacement = claim_job(db_engine, db_settings, "replacement")
    assert replacement.job_id == assigned.job_id
    result, second_effect = execute(replacement)
    assert (first_effect == second_effect) is protected
    report_outcome(
        db_engine,
        db_settings,
        replacement.attempt_id,
        CompleteRequest(
            worker_id="replacement",
            fencing_token=replacement.fencing_token,
            result=result,
        ),
    )
    assert effect_count(db_engine) == (1 if protected else 2)
    with pytest.raises(OwnershipConflict):
        report_outcome(
            db_engine,
            db_settings,
            assigned.attempt_id,
            CompleteRequest(
                worker_id="worker-a",
                fencing_token=assigned.fencing_token,
                result=first_result,
            ),
        )
    observations.append({"checkpoint": "stale_completion_rejected", "status_code": 409})
    assert get_job(db_engine, assigned.job_id).state == "succeeded"
    assert [a.state for a in get_attempts(db_engine, assigned.job_id).attempts] == [
        "expired",
        "succeeded",
    ]
    assert [e["kind"] for e in history(db_engine, assigned.job_id)] == [
        "submitted",
        "claimed",
        "expired",
        "claimed",
        "succeeded",
    ]
    output = request.config.getoption("--recordings-dir")
    if output:
        scenario = "effect-protected" if protected else "effect-unprotected"
        recording = capture_job(
            db_engine,
            db_settings,
            assigned.job_id,
            scenario=scenario,
            source_file=Path(__file__),
            source_label="backend/tests/integration/test_effects.py",
            observations=observations,
        )
        assert db_settings.api_token.get_secret_value() not in str(recording)
        assert db_settings.database_url.get_secret_value() not in str(recording)
        write_capture(Path(output) / f"{scenario}.json", recording)


def test_concurrent_protected_effects_commit_once(db_engine: Engine):
    start = Barrier(6)

    def execute(_):
        start.wait(timeout=10)
        return commit_effect(
            db_engine,
            business_key="shared-business-operation",
            units=1,
            job_id=uuid4(),
            attempt_id=uuid4(),
            protected=True,
        )

    with ThreadPoolExecutor(max_workers=6) as pool:
        results = list(pool.map(execute, range(6)))
    assert all(result == results[0] for result in results)
    assert effect_count(db_engine) == 1
    with pytest.raises(BusinessConflict):
        commit_effect(
            db_engine,
            business_key="shared-business-operation",
            units=2,
            job_id=uuid4(),
            attempt_id=uuid4(),
            protected=True,
        )
    assert effect_count(db_engine) == 1


def test_deduplication_marker_and_effect_rollback_together(db_engine: Engine):
    def fail_effect(conn, cursor, statement, parameters, context, executemany):
        if "INSERT INTO relevo_demo.effects" in statement:
            raise RuntimeError("controlled business transaction failure")

    event.listen(db_engine, "before_cursor_execute", fail_effect)
    try:
        with pytest.raises(RuntimeError, match="business transaction failure"):
            commit_effect(
                db_engine,
                business_key="atomic-business-operation",
                units=1,
                job_id=uuid4(),
                attempt_id=uuid4(),
                protected=True,
            )
    finally:
        event.remove(db_engine, "before_cursor_execute", fail_effect)
    with db_engine.connect() as connection:
        assert (
            connection.execute(text("SELECT count(*) FROM relevo_demo.operations")).scalar_one()
            == 0
        )
    assert effect_count(db_engine) == 0
    commit_effect(
        db_engine,
        business_key="atomic-business-operation",
        units=1,
        job_id=uuid4(),
        attempt_id=uuid4(),
        protected=True,
    )
    assert effect_count(db_engine) == 1

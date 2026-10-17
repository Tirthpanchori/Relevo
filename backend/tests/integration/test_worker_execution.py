"""Actual spawned handlers, HTTPX/ASGI adapters, and real PostgreSQL state transitions."""

import asyncio
import hashlib

import httpx
import pytest
from sqlalchemy import Engine, text

from relevo.api.app import create_app
from relevo.api.schemas import SubmitJob
from relevo.config import Settings
from relevo.engine.jobs import get_attempts, get_job, submit_job
from relevo.engine.recovery import recover_expired
from relevo.engine.serialization import canonical_json
from relevo.worker.config import WorkerSettings
from relevo.worker.coordinator import CoordinatorClient
from relevo.worker.runtime import Worker
from tests.integration.test_ownership import expire, make_eligible

pytestmark = pytest.mark.integration


def test_spawned_worker_completes_a_durable_job(db_engine: Engine, db_settings: Settings, tmp_path):
    payload = {"message": "real child, real database"}
    job, _ = submit_job(
        db_engine,
        db_settings,
        SubmitJob(
            task_type="hash_payload",
            payload=payload,
        ),
        "worker-end-to-end",
    )

    async def run():
        app = create_app(db_settings)
        settings = WorkerSettings(api_token=db_settings.api_token)
        async with (
            app.router.lifespan_context(app),
            CoordinatorClient(
                settings,
                transport=httpx.ASGITransport(app=app),
            ) as client,
        ):
            worker = Worker(client, settings, work_directory=tmp_path)
            assert await worker.run_once() == "reported"
            assert worker.active_process is None

    asyncio.run(run())
    stored = get_job(db_engine, job.id)
    assert stored.state == "succeeded"
    assert stored.result["sha256"] == hashlib.sha256(canonical_json(payload)).hexdigest()
    assert get_attempts(db_engine, job.id).attempts[0].state == "succeeded"


def test_worker_reports_failure_then_a_new_attempt_succeeds(
    db_engine: Engine,
    db_settings: Settings,
    tmp_path,
):
    job, _ = submit_job(
        db_engine,
        db_settings,
        SubmitJob(
            task_type="transient_failure",
            payload={"fail_attempts": 1},
        ),
        "worker-transient",
    )

    async def run():
        app = create_app(db_settings)
        settings = WorkerSettings(api_token=db_settings.api_token)
        async with (
            app.router.lifespan_context(app),
            CoordinatorClient(
                settings,
                transport=httpx.ASGITransport(app=app),
            ) as client,
        ):
            worker = Worker(client, settings, worker_id="first-instance", work_directory=tmp_path)
            assert await worker.run_once() == "reported"
            assert get_job(db_engine, job.id).state == "pending"
            with db_engine.begin() as connection:
                connection.execute(
                    text("""
                    UPDATE jobs SET available_at=clock_timestamp()-interval '1 second' WHERE id=:id
                """),
                    {"id": job.id},
                )
            replacement = Worker(
                client, settings, worker_id="replacement-instance", work_directory=tmp_path
            )
            assert await replacement.run_once() == "reported"

    asyncio.run(run())
    assert get_job(db_engine, job.id).state == "succeeded"
    attempts = get_attempts(db_engine, job.id).attempts
    assert [attempt.state for attempt in attempts] == ["failed", "succeeded"]
    assert [attempt.worker_id for attempt in attempts] == ["first-instance", "replacement-instance"]


def test_lost_claim_response_is_recovered_without_speculative_execution(
    db_engine: Engine, db_settings: Settings, tmp_path
):
    job, _ = submit_job(
        db_engine, db_settings, SubmitJob(task_type="hash_payload", payload={}), "lost-worker-claim"
    )

    async def run():
        app = create_app(db_settings)
        settings = WorkerSettings(api_token=db_settings.api_token)
        transport = httpx.ASGITransport(app=app)

        async def lose_claim(request):
            response = await transport.handle_async_request(request)
            await response.aread()
            assert response.status_code == 200
            raise httpx.ReadTimeout("Controlled response loss after committed claim")

        async with app.router.lifespan_context(app):
            async with CoordinatorClient(
                settings, transport=httpx.MockTransport(lose_claim)
            ) as client:
                worker = Worker(client, settings, worker_id="uncertain", work_directory=tmp_path)
                assert await worker.run_once() == "unavailable"
                assert worker.active_process is None and list(tmp_path.iterdir()) == []
            first = get_attempts(db_engine, job.id).attempts[0]
            assert first.state == "running" and first.worker_id == "uncertain"
            expire(db_engine, first.id)
            assert recover_expired(db_engine, db_settings)[0].state == "pending"
            make_eligible(db_engine, job.id)
            async with CoordinatorClient(settings, transport=transport) as client:
                replacement = Worker(client, settings, work_directory=tmp_path)
                assert await replacement.run_once() == "reported"

    asyncio.run(run())
    assert get_job(db_engine, job.id).state == "succeeded"
    assert [a.state for a in get_attempts(db_engine, job.id).attempts] == ["expired", "succeeded"]

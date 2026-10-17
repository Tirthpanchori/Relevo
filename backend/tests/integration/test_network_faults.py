"""TCP faults target only test API/database links, never development-service connections."""

import asyncio
import os
from threading import Event
from time import monotonic

import httpx
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import Engine, text
from sqlalchemy.engine import make_url

from relevo.api.app import create_app
from relevo.api.schemas import CompleteRequest, FailRequest, SubmitJob, TaskError
from relevo.client import ClientSettings, ClientUnavailable, RelevoClient
from relevo.config import Settings
from relevo.engine.jobs import get_attempts, get_job
from relevo.engine.ownership import report_outcome
from relevo.engine.recovery import recover_expired
from relevo.worker.config import WorkerSettings
from relevo.worker.coordinator import CoordinatorClient, CoordinatorUnavailable
from relevo.worker.runtime import Worker
from tests.integration.test_ownership import create_assignment, expire, history, make_eligible

pytestmark = [pytest.mark.integration, pytest.mark.network]


@pytest.fixture
def proxy(db_engine: Engine, db_settings: Settings):
    url = os.environ.get("RELEVO_TOXIPROXY_URL")
    if not url:
        pytest.skip("Run through the Compose test profile for controlled TCP faults")
    assert (
        make_url(os.environ["RELEVO_PROXY_DATABASE_URL"]).database
        == make_url(db_settings.database_url.get_secret_value()).database
    ), "The proxy must target the same dedicated *_test database"
    with httpx.Client(base_url=url, timeout=3, trust_env=False) as admin:
        deadline = monotonic() + 15
        while True:
            try:
                admin.get("/version").raise_for_status()
                break
            except httpx.TransportError:
                assert monotonic() < deadline, "Toxiproxy did not start"
                Event().wait(0.05)
        admin.post("/reset").raise_for_status()
        try:
            with httpx.Client(
                base_url=os.environ["RELEVO_PROXY_API_URL"], timeout=1, trust_env=False
            ) as api:
                while True:
                    try:
                        response = api.get("/health/ready")
                        if response.status_code == 200:
                            break
                    except httpx.TransportError:
                        pass
                    assert monotonic() < deadline, "Fault-test API did not become ready"
                    Event().wait(0.05)
            yield admin
        finally:
            admin.post("/reset").raise_for_status()


def toxic(admin, name, type_, attributes):
    admin.post(
        "/proxies/relevo_test_api/toxics",
        json={
            "name": name,
            "type": type_,
            "stream": "downstream",
            "toxicity": 1,
            "attributes": attributes,
        },
    ).raise_for_status()


def test_tcp_lost_submission_response_replays_the_committed_job(proxy, db_engine, db_settings):
    toxic(proxy, "lost-acceptance", "timeout", {"timeout": 0})
    request = SubmitJob(task_type="hash_payload", payload={"transport": "real-tcp"})

    async def run():
        async with RelevoClient(
            ClientSettings(
                api_url=os.environ["RELEVO_PROXY_API_URL"],
                api_token=db_settings.api_token,
                http_timeout_seconds=0.3,
                submission_attempts=1,
            )
        ) as client:
            with pytest.raises(ClientUnavailable):
                await client.submit(request, idempotency_key="tcp-lost-acceptance")
            with db_engine.connect() as connection:
                job_id = connection.execute(text("SELECT id FROM jobs")).scalar_one()
            assert len(history(db_engine, job_id)) == 1
            proxy.delete("/proxies/relevo_test_api/toxics/lost-acceptance").raise_for_status()
            job = await client.submit(request, idempotency_key="tcp-lost-acceptance")
            assert job.id == job_id and len(history(db_engine, job_id)) == 1

    asyncio.run(run())


@pytest.mark.parametrize("kind", ["complete", "fail"])
def test_tcp_lost_outcome_response_replays_one_committed_transition(
    proxy, db_engine, db_settings, kind
):
    assigned = create_assignment(db_engine, db_settings)
    owner = {"worker_id": "worker-a", "fencing_token": assigned.fencing_token}
    report = (
        CompleteRequest(**owner, result={"finished": True})
        if kind == "complete"
        else FailRequest(
            **owner, error=TaskError(code="transient", message="Retry"), retryable=True
        )
    )
    toxic(proxy, "lost-outcome", "timeout", {"timeout": 0})

    async def run():
        settings = WorkerSettings(
            api_url=os.environ["RELEVO_PROXY_API_URL"],
            api_token=db_settings.api_token,
            http_timeout_seconds=0.3,
        )
        async with CoordinatorClient(settings) as client:
            with pytest.raises(CoordinatorUnavailable):
                await client.report(assigned.attempt_id, kind, report.model_dump(mode="json"))
            committed = history(db_engine, assigned.job_id)
            assert len(committed) == 3 and committed[-1]["kind"] in ("succeeded", "failed")
            proxy.delete("/proxies/relevo_test_api/toxics/lost-outcome").raise_for_status()
            acknowledged = await client.report(
                assigned.attempt_id, kind, report.model_dump(mode="json")
            )
            assert acknowledged == report_outcome(
                db_engine, db_settings, assigned.attempt_id, report
            )
            assert history(db_engine, assigned.job_id) == committed

    asyncio.run(run())


def test_database_tcp_disconnect_cannot_acknowledge_new_work_and_reconnects(
    proxy, db_engine, db_settings
):
    settings = Settings(
        **{
            **db_settings.model_dump(),
            "database_url": os.environ["RELEVO_PROXY_DATABASE_URL"],
            "db_connect_timeout_seconds": 1,
        }
    )
    with TestClient(create_app(settings)) as api:
        api.headers["Authorization"] = f"Bearer {db_settings.api_token.get_secret_value()}"
        body = {"task_type": "hash_payload", "payload": {"durable": True}}
        first = api.post("/jobs", json=body, headers={"Idempotency-Key": "before-disconnect"})
        assert first.status_code == 201
        proxy.post("/proxies/relevo_test_database", json={"enabled": False}).raise_for_status()
        assert api.get("/health/ready").status_code == 503
        uncertain = api.post("/jobs", json=body, headers={"Idempotency-Key": "during-disconnect"})
        assert uncertain.status_code == 503
        proxy.post("/proxies/relevo_test_database", json={"enabled": True}).raise_for_status()
        assert api.get(f"/jobs/{first.json()['id']}").status_code == 200
        assert api.get("/health/ready").status_code == 200
    with db_engine.connect() as connection:
        assert connection.execute(text("SELECT count(*) FROM jobs")).scalar_one() == 1


def test_tcp_delayed_heartbeat_stops_child_then_replacement_completes(
    proxy, db_engine, db_settings, tmp_path
):
    from relevo.engine.jobs import submit_job

    job, _ = submit_job(
        db_engine,
        db_settings,
        SubmitJob(task_type="timed_work", payload={"duration_seconds": 1}),
        "tcp-heartbeat",
    )

    class PartitionAfterClaim(CoordinatorClient):
        async def claim(self, worker_id):
            assigned = await super().claim(worker_id)
            assert assigned is not None
            toxic(proxy, "late-heartbeat", "latency", {"latency": 2_000, "jitter": 0})
            return assigned

    async def run():
        settings = WorkerSettings(
            api_url=os.environ["RELEVO_PROXY_API_URL"],
            api_token=db_settings.api_token,
            heartbeat_seconds=0.1,
            http_timeout_seconds=0.3,
        )
        async with PartitionAfterClaim(settings) as client:
            worker = Worker(client, settings, work_directory=tmp_path)
            assert await asyncio.wait_for(worker.run_once(), timeout=5) == "ownership_lost"
            assert worker.active_process is None and list(tmp_path.iterdir()) == []
        assert get_job(db_engine, job.id).state == "running"
        first = get_attempts(db_engine, job.id).attempts[0]
        proxy.delete("/proxies/relevo_test_api/toxics/late-heartbeat").raise_for_status()
        expire(db_engine, first.id)
        assert len(recover_expired(db_engine, db_settings)) == 1
        make_eligible(db_engine, job.id)
        async with CoordinatorClient(settings) as client:
            replacement = Worker(client, settings, work_directory=tmp_path)
            assert await replacement.run_once() == "reported"

    asyncio.run(run())
    assert get_job(db_engine, job.id).state == "succeeded"
    assert [a.state for a in get_attempts(db_engine, job.id).attempts] == ["expired", "succeeded"]

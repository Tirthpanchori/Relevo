"""No sockets/database: actual spawned handlers with a controlled HTTPX transport."""

import asyncio
import json
from datetime import UTC, datetime, timedelta
from time import monotonic
from uuid import uuid4

import httpx
import pytest
from pydantic import ValidationError

from relevo.worker.config import WorkerSettings
from relevo.worker.coordinator import CoordinatorClient, CoordinatorRejected, CoordinatorUnavailable
from relevo.worker.runtime import Worker


def worker_settings(**overrides) -> WorkerSettings:
    return WorkerSettings(api_token="test-worker-token-never-use-in-production-123", **overrides)


def assignment(**overrides) -> dict:
    now = datetime.now(UTC)
    return {
        "job_id": str(uuid4()),
        "attempt_id": str(uuid4()),
        "attempt_number": 1,
        "fencing_token": 1,
        "lease_expires_at": (now + timedelta(seconds=15)).isoformat(),
        "task_type": "hash_payload",
        "payload": {"hello": "world"},
        "task_timeout_seconds": 10,
        "lease_seconds": 15,
        "max_result_bytes": 65_536,
        **overrides,
    }


class FakeCoordinator:
    def __init__(self, claim=None, *, lose_reports=0, heartbeat_status=200, block_heartbeat=False):
        self.claim = claim
        self.lose_reports = lose_reports
        self.heartbeat_status = heartbeat_status
        self.block_heartbeat = block_heartbeat
        self.reports = []
        self.heartbeats = 0
        self.claims = 0

    async def __call__(self, request):
        if request.url.path == "/internal/claim":
            self.claims += 1
            return (
                httpx.Response(204) if self.claim is None else httpx.Response(200, json=self.claim)
            )
        if request.url.path.endswith("/heartbeat"):
            self.heartbeats += 1
            if self.block_heartbeat:
                await asyncio.Event().wait()
            return httpx.Response(
                self.heartbeat_status,
                json={
                    "attempt_id": self.claim["attempt_id"],
                    "lease_seconds": self.claim["lease_seconds"],
                    "lease_expires_at": self.claim["lease_expires_at"],
                },
            )
        self.reports.append((request.url.path, json.loads(request.content)))
        if self.lose_reports:
            self.lose_reports -= 1
            raise httpx.ReadTimeout("controlled lost response")
        return httpx.Response(
            200,
            json={
                "job_id": self.claim["job_id"],
                "attempt_id": self.claim["attempt_id"],
                "state": "succeeded" if request.url.path.endswith("/complete") else "failed",
                "available_at": datetime.now(UTC).isoformat(),
            },
        )


def run_assignment(tmp_path, fake: FakeCoordinator, **overrides):
    async def run():
        settings = worker_settings(**overrides)
        async with CoordinatorClient(settings, transport=httpx.MockTransport(fake)) as client:
            worker = Worker(client, settings, worker_id="worker-test", work_directory=tmp_path)
            outcome = await worker.run_once()
            assert worker.active_process is None
            assert list(tmp_path.iterdir()) == []
            return outcome

    return asyncio.run(run())


def test_worker_claims_and_runs_a_real_spawned_hash_handler(tmp_path):
    fake = FakeCoordinator(assignment())
    assert run_assignment(tmp_path, fake) == "reported"
    assert fake.claims == 1 and len(fake.reports) == 1
    assert fake.reports[0][0].endswith("/complete")
    assert len(fake.reports[0][1]["result"]["sha256"]) == 64
    assert fake.reports[0][1]["worker_id"] == "worker-test"


def test_worker_idle_does_not_start_a_process(tmp_path):
    fake = FakeCoordinator()
    assert run_assignment(tmp_path, fake) == "idle"
    assert not fake.reports


@pytest.mark.parametrize("timing", ["invalid", -1, float("inf"), True])
def test_optional_timing_metadata_cannot_change_a_valid_outcome(tmp_path, monkeypatch, timing):
    from relevo.worker import runtime

    original = runtime.read_result

    def with_bad_timing(*args):
        return {**original(*args), "_handler_seconds": timing}

    monkeypatch.setattr(runtime, "read_result", with_bad_timing)
    fake = FakeCoordinator(assignment())
    assert run_assignment(tmp_path, fake) == "reported"
    assert fake.reports[0][0].endswith("/complete")
    assert "_handler_seconds" not in fake.reports[0][1]


@pytest.mark.parametrize(
    "task,payload,code,retryable",
    [
        ("transient_failure", {"fail_attempts": 1}, "configured_failure", True),
        ("timed_work", {"duration_seconds": -1}, "invalid_payload", False),
    ],
)
def test_handler_failures_have_explicit_retry_policy(tmp_path, task, payload, code, retryable):
    fake = FakeCoordinator(assignment(task_type=task, payload=payload))
    assert run_assignment(tmp_path, fake) == "reported"
    assert fake.reports[0][0].endswith("/fail")
    assert fake.reports[0][1]["error"]["code"] == code
    assert fake.reports[0][1]["retryable"] is retryable


def test_result_limit_is_enforced_before_reporting(tmp_path):
    fake = FakeCoordinator(assignment(max_result_bytes=1))
    assert run_assignment(tmp_path, fake) == "reported"
    assert fake.reports[0][1]["error"]["code"] == "result_too_large"
    assert not fake.reports[0][1]["retryable"]


def test_execution_timeout_stops_child_and_reports_retryable_failure(tmp_path):
    fake = FakeCoordinator(
        assignment(
            task_type="timed_work",
            payload={"duration_seconds": 10},
            task_timeout_seconds=0.5,
        )
    )
    started = monotonic()
    assert run_assignment(tmp_path, fake) == "reported"
    assert monotonic() - started < 5
    assert fake.reports[0][1]["error"]["code"] == "execution_timeout"
    assert fake.reports[0][1]["retryable"]


@pytest.mark.parametrize("mode", ["rejected", "unconfirmed"])
def test_ownership_loss_stops_child_without_a_new_outcome(tmp_path, mode):
    fake = FakeCoordinator(
        assignment(task_type="timed_work", payload={"duration_seconds": 10}),
        heartbeat_status=409 if mode == "rejected" else 200,
        block_heartbeat=mode == "unconfirmed",
    )
    started = monotonic()
    assert (
        run_assignment(tmp_path, fake, heartbeat_seconds=0.05, http_timeout_seconds=0.1)
        == "ownership_lost"
    )
    assert monotonic() - started < 5
    assert fake.heartbeats >= 1 and fake.reports == []


def test_slow_handler_keeps_renewing_while_it_runs(tmp_path):
    fake = FakeCoordinator(assignment(task_type="timed_work", payload={"duration_seconds": 0.5}))
    assert run_assignment(tmp_path, fake, heartbeat_seconds=0.05) == "reported"
    assert fake.heartbeats >= 1 and fake.reports[0][0].endswith("/complete")


def test_lost_report_is_retried_with_identical_body_and_no_second_execution(tmp_path):
    fake = FakeCoordinator(
        assignment(task_type="transient_failure", payload={"fail_attempts": 0}), lose_reports=2
    )
    assert run_assignment(tmp_path, fake) == "reported"
    assert fake.claims == 1 and len(fake.reports) == 3
    assert all(report == fake.reports[0] for report in fake.reports)


def test_exhausted_report_delivery_does_not_execute_again(tmp_path):
    fake = FakeCoordinator(assignment(), lose_reports=10)
    assert run_assignment(tmp_path, fake) == "unavailable"
    assert fake.claims == 1 and len(fake.reports) == 3
    assert all(report == fake.reports[0] for report in fake.reports)


def test_uncertain_claim_is_not_retried_or_executed(tmp_path):
    claims = []

    def fail_claim(request):
        claims.append(request)
        raise httpx.ReadTimeout("controlled claim uncertainty")

    async def run():
        settings = worker_settings()
        async with CoordinatorClient(settings, transport=httpx.MockTransport(fail_claim)) as client:
            worker = Worker(client, settings, work_directory=tmp_path)
            assert await worker.run_once() == "unavailable"
            assert worker.active_process is None

    asyncio.run(run())
    assert len(claims) == 1 and list(tmp_path.iterdir()) == []


def test_shutdown_stops_the_active_child(tmp_path):
    async def run():
        fake = FakeCoordinator(assignment(task_type="timed_work", payload={"duration_seconds": 10}))
        settings = worker_settings()
        async with CoordinatorClient(settings, transport=httpx.MockTransport(fake)) as client:
            worker = Worker(client, settings, work_directory=tmp_path)
            task = asyncio.create_task(worker.run_once())
            async with asyncio.timeout(5):
                while worker.active_process is None:
                    assert not task.done(), "worker exited before starting its child"
                    await asyncio.sleep(0.005)
            worker.stop.set()
            assert await asyncio.wait_for(task, timeout=5) == "ownership_lost"
            assert worker.active_process is None and fake.reports == []

    asyncio.run(run())


def test_total_http_deadline_cancels_a_stalled_response():
    async def stalled(request):
        await asyncio.Event().wait()

    async def run():
        settings = worker_settings(http_timeout_seconds=0.05)
        async with CoordinatorClient(settings, transport=httpx.MockTransport(stalled)) as client:
            with pytest.raises(CoordinatorUnavailable):
                await asyncio.wait_for(client.claim("worker"), timeout=1)

    asyncio.run(run())


@pytest.mark.parametrize(
    "url",
    ["https://user:password@example.com", "http://localhost/jobs", "http://localhost?token=x"],
)
def test_worker_configuration_rejects_non_origin_urls(url):
    with pytest.raises(ValidationError):
        worker_settings(api_url=url)


def test_worker_rejects_malformed_or_oversized_coordinator_responses():
    async def run(response):
        settings = worker_settings()
        async with CoordinatorClient(
            settings, transport=httpx.MockTransport(lambda request: response)
        ) as client:
            with pytest.raises(CoordinatorRejected):
                await client.claim("worker")

    asyncio.run(run(httpx.Response(200, json={"invalid": "claim"})))
    asyncio.run(run(httpx.Response(200, content=b"x" * 1_048_577)))

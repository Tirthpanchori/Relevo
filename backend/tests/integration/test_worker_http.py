"""Exercise real HTTP adapters, including responses lost after transactional commit."""

from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import Engine

from relevo.config import Settings
from relevo.engine.jobs import get_attempts, get_job

from .test_ownership import create_assignment, expire, history

pytestmark = pytest.mark.integration


def test_worker_http_lifecycle(api_client: TestClient):
    submitted = api_client.post(
        "/jobs",
        json={"task_type": "hash_payload", "payload": {"message": "hello"}},
        headers={"Idempotency-Key": "http-flow"},
    )
    assignment = api_client.post("/internal/claim", json={"worker_id": "http-worker"})
    assert assignment.status_code == 200
    claim = assignment.json()
    assert claim["job_id"] == submitted.json()["id"]
    assert claim["task_type"] == "hash_payload" and claim["payload"] == {"message": "hello"}
    assert claim["attempt_number"] == claim["fencing_token"] == 1
    attempt_path = f"/internal/attempts/{claim['attempt_id']}"
    ownership = {"worker_id": "http-worker", "fencing_token": claim["fencing_token"]}
    heartbeat = api_client.post(f"{attempt_path}/heartbeat", json=ownership)
    assert heartbeat.status_code == 200
    body = {**ownership, "result": {"hash": "reported-result"}}
    first = api_client.post(f"{attempt_path}/complete", json=body)
    replay = api_client.post(f"{attempt_path}/complete", json=body)
    assert first.status_code == replay.status_code == 200
    assert first.json() == replay.json()
    assert first.json()["state"] == "succeeded"
    assert api_client.get(f"/jobs/{claim['job_id']}").json()["result"] == body["result"]
    assert (
        api_client.get(f"/jobs/{claim['job_id']}/attempts").json()["attempts"][0]["state"]
        == "succeeded"
    )


@pytest.mark.parametrize("kind", ["complete", "fail"])
def test_lost_report_response_replays_without_another_transition(
    api_client: TestClient,
    db_engine: Engine,
    db_settings: Settings,
    kind: str,
):
    assignment = create_assignment(db_engine, db_settings)
    body = {"worker_id": "worker-a", "fencing_token": assignment.fencing_token}
    body.update(
        {"result": {"done": True}}
        if kind == "complete"
        else {
            "error": {"code": "controlled", "message": "failure"},
            "retryable": True,
        }
    )
    path = f"/internal/attempts/{assignment.attempt_id}/{kind}"
    transport = api_client._transport
    original_outcomes = []

    class DropResponse:
        def handle_request(self, request):
            response = transport.handle_request(request)
            response.read()
            original_outcomes.append(response.json())
            response.close()
            raise ConnectionError("controlled lost report response")

    api_client._transport = DropResponse()
    try:
        with pytest.raises(ConnectionError, match="lost report response"):
            api_client.post(path, json=body)
    finally:
        api_client._transport = transport
    assert len(history(db_engine, assignment.job_id)) == 3
    expire(db_engine, assignment.attempt_id)
    response = api_client.post(path, json=body)
    assert response.status_code == 200 and response.json() == original_outcomes[0]
    assert len(history(db_engine, assignment.job_id)) == 3
    assert get_job(db_engine, assignment.job_id).attempt_count == 1


@pytest.mark.parametrize("operation", ["heartbeat", "complete", "fail"])
def test_unknown_attempt_returns_not_found(api_client: TestClient, operation: str):
    body = {"worker_id": "worker-a", "fencing_token": 1}
    if operation == "complete":
        body["result"] = None
    if operation == "fail":
        body.update({"error": {"code": "test", "message": "test"}, "retryable": False})
    response = api_client.post(f"/internal/attempts/{uuid4()}/{operation}", json=body)
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "attempt_not_found"


def test_expired_http_ownership_is_conflict(
    api_client: TestClient,
    db_engine: Engine,
    db_settings: Settings,
):
    assignment = create_assignment(db_engine, db_settings)
    expire(db_engine, assignment.attempt_id)
    response = api_client.post(
        f"/internal/attempts/{assignment.attempt_id}/heartbeat",
        json={
            "worker_id": "worker-a",
            "fencing_token": assignment.fencing_token,
        },
    )
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "ownership_conflict"


def test_invalid_report_cannot_be_persisted(
    api_client: TestClient,
    db_engine: Engine,
    db_settings: Settings,
):
    assignment = create_assignment(db_engine, db_settings)
    path = f"/internal/attempts/{assignment.attempt_id}"
    assert (
        api_client.post(
            f"{path}/fail",
            json={
                "worker_id": "worker-a",
                "fencing_token": assignment.fencing_token,
                "error": {"code": "invalid", "message": "bad\x00message"},
                "retryable": False,
            },
        ).status_code
        == 422
    )
    assert (
        api_client.post(
            f"{path}/complete",
            json={
                "worker_id": "worker-a",
                "fencing_token": 2**100,
                "result": None,
            },
        ).status_code
        == 422
    )
    assert (
        api_client.post(
            f"{path}/complete",
            json={
                "worker_id": "worker-a",
                "fencing_token": assignment.fencing_token,
                "result": "x" * 65_536,
            },
        ).status_code
        == 413
    )
    assert get_attempts(db_engine, assignment.job_id).attempts[0].state == "running"
    assert len(history(db_engine, assignment.job_id)) == 2

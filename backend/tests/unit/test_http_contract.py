from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from relevo.api.app import create_app
from relevo.config import Settings

from ..conftest import TEST_TOKEN


def test_exact_routes_and_ownership_contracts(unit_settings: Settings) -> None:
    app = create_app(unit_settings)
    schema = app.openapi()
    assert set(schema["paths"]) == {
        "/jobs",
        "/jobs/{id}",
        "/jobs/{id}/attempts",
        "/internal/claim",
        "/internal/attempts/{id}/heartbeat",
        "/internal/attempts/{id}/complete",
        "/internal/attempts/{id}/fail",
        "/health/live",
        "/health/ready",
        "/metrics",
    }
    assert "204" in schema["paths"]["/internal/claim"]["post"]["responses"]
    for path, operations in schema["paths"].items():
        if path.startswith("/internal/"):
            assert "501" not in operations["post"]["responses"]
            assert "409" in operations["post"]["responses"]


@pytest.mark.parametrize(
    "method,path,body",
    [
        ("POST", "/jobs", {"task_type": "hash_payload", "payload": {}}),
        ("GET", f"/jobs/{uuid4()}", None),
        ("GET", f"/jobs/{uuid4()}/attempts", None),
        ("POST", "/internal/claim", {"worker_id": "worker-a"}),
        ("POST", f"/internal/attempts/{uuid4()}/heartbeat", {"worker_id": "w", "fencing_token": 1}),
        (
            "POST",
            f"/internal/attempts/{uuid4()}/complete",
            {"worker_id": "w", "fencing_token": 1, "result": None},
        ),
        (
            "POST",
            f"/internal/attempts/{uuid4()}/fail",
            {
                "worker_id": "w",
                "fencing_token": 1,
                "error": {"code": "test", "message": "test"},
                "retryable": True,
            },
        ),
        ("GET", "/metrics", None),
    ],
)
def test_protected_routes_require_token(
    unit_settings: Settings,
    method: str,
    path: str,
    body: dict | None,
) -> None:
    with TestClient(create_app(unit_settings)) as client:
        response = client.request(method, path, json=body)
        assert response.status_code == 401
        assert response.headers["www-authenticate"] == "Bearer"


def test_liveness_independent_of_database_and_readiness_fails_closed(
    unit_settings: Settings,
) -> None:
    with TestClient(create_app(unit_settings)) as client:
        assert client.get("/health/live").json() == {"status": "ok"}
        ready = client.get("/health/ready")
        assert ready.status_code == 503
        assert ready.json() == {"status": "not_ready"}


def test_validation_errors_do_not_echo_payload_or_token(unit_settings: Settings) -> None:
    with TestClient(create_app(unit_settings)) as client:
        response = client.post(
            "/jobs",
            json={"task_type": "private-unknown-handler", "payload": {}},
            headers={"Authorization": f"Bearer {TEST_TOKEN}", "Idempotency-Key": "safe-key"},
        )
        assert response.status_code == 422
        assert "private-unknown-handler" not in response.text
        assert TEST_TOKEN not in response.text


def test_oversized_raw_body_rejected_before_json_decode(unit_settings: Settings) -> None:
    with TestClient(create_app(unit_settings)) as client:
        response = client.post(
            "/jobs",
            content=b"x" * (unit_settings.max_request_bytes + 1),
            headers={"Content-Type": "application/json"},
        )
        assert response.status_code == 413
        assert response.json()["error"]["code"] == "size_limit_exceeded"


def test_chunked_body_limit_cannot_be_bypassed(unit_settings: Settings) -> None:
    with TestClient(create_app(unit_settings)) as client:
        response = client.post(
            "/jobs",
            content=iter([b"x" * 600_000, b"x" * 600_000]),
            headers={"Content-Type": "application/json"},
        )
        assert response.status_code == 413


def test_database_failure_does_not_acknowledge_submission(unit_settings: Settings) -> None:
    with TestClient(create_app(unit_settings)) as client:
        response = client.post(
            "/jobs",
            json={"task_type": "hash_payload", "payload": {}},
            headers={"Authorization": f"Bearer {TEST_TOKEN}", "Idempotency-Key": "no-db"},
        )
        assert response.status_code == 503
        assert response.json()["error"]["code"] == "database_unavailable"
        assert "unused" not in response.text

"""Verify the actual running API without exposing the environment-provided token."""

import os
from uuid import uuid4

import httpx


def main() -> None:
    token = os.environ.get("RELEVO_API_TOKEN")
    if not token:
        raise SystemExit("RELEVO_API_TOKEN must be supplied through the environment")
    base_url = os.environ.get("RELEVO_API_URL", "http://127.0.0.1:8000")
    with httpx.Client(
        base_url=base_url,
        headers={"Authorization": f"Bearer {token}"},
        timeout=10,
        trust_env=False,
    ) as client:
        assert client.get("/health/live").json() == {"status": "ok"}
        ready = client.get("/health/ready")
        assert ready.status_code == 200 and ready.json() == {"status": "ready"}
        key = f"smoke-{uuid4()}"
        request = {"task_type": "hash_payload", "payload": {"source": "smoke-check"}}
        first = client.post("/jobs", json=request, headers={"Idempotency-Key": key})
        assert first.status_code == 201, first.text
        replay = client.post("/jobs", json=request, headers={"Idempotency-Key": key})
        assert replay.status_code == 200, replay.text
        job_id = first.json()["id"]
        assert replay.json()["id"] == job_id
        assert client.get(f"/jobs/{job_id}").json()["id"] == job_id
        assert client.get(f"/jobs/{job_id}/attempts").status_code == 200
        assert (
            client.post(
                "/jobs",
                json={**request, "payload": {"different": True}},
                headers={"Idempotency-Key": key},
            ).status_code
            == 409
        )
        assert client.get("/metrics").status_code == 200
        print(f"Live API checks passed; durable job {job_id} is inspectable.")


if __name__ == "__main__":
    main()

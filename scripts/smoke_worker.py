"""Exercise the installed worker through the real HTTP API without printing secrets."""

import hashlib
import json
import os
import time
from uuid import uuid4

import httpx


def main() -> None:
    token = os.environ.get("RELEVO_API_TOKEN")
    if not token:
        raise SystemExit("RELEVO_API_TOKEN must be supplied through the environment")
    with httpx.Client(
        base_url=os.environ.get("RELEVO_API_URL", "http://127.0.0.1:8000"),
        headers={"Authorization": f"Bearer {token}"},
        timeout=5,
        trust_env=False,
    ) as client:
        payload = {"source": "installed-worker-smoke"}
        submitted = []
        for task_type, task_payload in (
            ("hash_payload", payload),
            ("transient_failure", {"fail_attempts": 1}),
        ):
            response = client.post(
                "/jobs",
                json={"task_type": task_type, "payload": task_payload},
                headers={"Idempotency-Key": f"worker-smoke-{uuid4()}"},
            )
            response.raise_for_status()
            submitted.append(response.json()["id"])

        deadline = time.monotonic() + 45
        completed = []
        while time.monotonic() < deadline:
            completed = []
            for job_id in submitted:
                response = client.get(f"/jobs/{job_id}")
                response.raise_for_status()
                job = response.json()
                assert job["state"] != "failed", f"Smoke job {job_id} failed"
                completed.append(job)
            if all(job["state"] == "succeeded" for job in completed):
                break
            time.sleep(0.1)
        else:
            raise SystemExit(
                "Installed worker did not finish smoke jobs within 45 seconds"
            )

        expected = hashlib.sha256(
            json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()
        assert completed[0]["result"]["sha256"] == expected
        worker_ids = set()
        for number, job_id in enumerate(submitted):
            response = client.get(f"/jobs/{job_id}/attempts")
            response.raise_for_status()
            attempts = response.json()["attempts"]
            assert [attempt["state"] for attempt in attempts] == (
                ["succeeded"] if number == 0 else ["failed", "succeeded"]
            )
            worker_ids.update(attempt["worker_id"] for attempt in attempts)
        print(
            f"Installed worker checks passed: jobs={submitted}, workers={sorted(worker_ids)}"
        )


if __name__ == "__main__":
    main()

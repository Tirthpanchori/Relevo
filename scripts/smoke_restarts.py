"""Development Compose proof of coordinator/database restart with surviving storage."""

import argparse
import os
import subprocess
import time
from pathlib import Path
from uuid import UUID, uuid4

import httpx

ROOT = Path(__file__).resolve().parents[1]


def compose(*args):
    subprocess.run(
        ["docker", "compose", *args],
        cwd=ROOT,
        capture_output=True,
        check=True,
        timeout=30,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--recording", type=Path)
    args = parser.parse_args()
    token = os.environ.get("RELEVO_API_TOKEN")
    if not token:
        raise SystemExit("RELEVO_API_TOKEN must be supplied through the environment")
    observations = []
    with httpx.Client(
        base_url="http://127.0.0.1:8000",
        headers={"Authorization": f"Bearer {token}"},
        timeout=5,
        trust_env=False,
    ) as client:

        def ready():
            deadline = time.monotonic() + 25
            while time.monotonic() < deadline:
                try:
                    if client.get("/health/ready").status_code == 200:
                        return
                except httpx.TransportError:
                    pass
                time.sleep(0.1)
            raise SystemExit(
                "Coordinator/database did not return to ready within 25 seconds"
            )

        def submit(key, body):
            response = client.post("/jobs", json=body, headers={"Idempotency-Key": key})
            response.raise_for_status()
            return response.json()

        def wait(job_id):
            deadline = time.monotonic() + 15
            while time.monotonic() < deadline:
                response = client.get(f"/jobs/{job_id}")
                response.raise_for_status()
                job = response.json()
                assert job["state"] != "failed"
                if job["state"] == "succeeded":
                    return job
                time.sleep(0.1)
            raise SystemExit("Restarted services did not complete the saved job")

        ready()
        terminal_key, pending_key = f"terminal-{uuid4()}", f"pending-{uuid4()}"
        terminal_body = {
            "task_type": "hash_payload",
            "payload": {"source": "restart-terminal"},
        }
        pending_body = {
            "task_type": "hash_payload",
            "payload": {"source": "restart-pending"},
        }
        terminal = wait(submit(terminal_key, terminal_body)["id"])
        compose("stop", "worker")
        try:
            pending = submit(pending_key, pending_body)
            assert pending["state"] == "pending"
            compose("stop", "api")
            try:
                client.post(
                    "/jobs", json=pending_body, headers={"Idempotency-Key": pending_key}
                )
            except httpx.TransportError:
                observations.append(
                    {"checkpoint": "api_stopped_request_not_acknowledged"}
                )
            else:
                raise AssertionError("Stopped API unexpectedly acknowledged a request")
            compose("start", "api")
            ready()
            assert submit(pending_key, pending_body)["id"] == pending["id"]
            assert client.get(f"/jobs/{terminal['id']}").json() == terminal
            observations.append(
                {"checkpoint": "api_restart_preserved_pending_and_terminal_jobs"}
            )

            compose("stop", "postgres")
            assert client.get("/health/live").status_code == 200
            assert client.get("/health/ready").status_code == 503
            failed_key = f"database-off-{uuid4()}"
            response = client.post(
                "/jobs", json=pending_body, headers={"Idempotency-Key": failed_key}
            )
            assert response.status_code == 503
            observations.append(
                {
                    "checkpoint": "database_stopped_submission_unconfirmed",
                    "status_code": 503,
                }
            )
            compose("start", "postgres")
            ready()
            assert client.get(f"/jobs/{terminal['id']}").json() == terminal
            assert client.get(f"/jobs/{pending['id']}").json()["state"] == "pending"
            assert submit(pending_key, pending_body)["id"] == pending["id"]
            observations.append(
                {"checkpoint": "database_restart_preserved_both_acknowledged_jobs"}
            )
            compose("kill", "--signal", "SIGKILL", "postgres")
            compose("start", "postgres")
            ready()
            assert client.get(f"/jobs/{terminal['id']}").json() == terminal
            assert client.get(f"/jobs/{pending['id']}").json()["state"] == "pending"
            observations.append(
                {
                    "checkpoint": "database_sigkill_recovery_preserved_both_acknowledged_jobs"
                }
            )
            compose("start", "worker")
            completed = wait(pending["id"])
            assert completed["attempt_count"] == 1
            assert client.get(f"/jobs/{terminal['id']}").json() == terminal
            if args.recording:
                from relevo.config import Settings
                from relevo.db.connection import build_engine
                from relevo.demo.recordings import capture_job, write_capture

                settings = Settings()
                engine = build_engine(settings)
                try:
                    recording = capture_job(
                        engine,
                        settings,
                        UUID(pending["id"]),
                        scenario="component-restarts",
                        source_file=Path(__file__),
                        source_label="scripts/smoke_restarts.py",
                        observations=observations,
                    )
                    recording["also_verified_terminal_job_id"] = terminal["id"]
                    write_capture(args.recording, recording)
                finally:
                    engine.dispose()
            print(
                "Coordinator/database restart checks passed; both acknowledged jobs survived."
            )
        finally:
            compose("start", "postgres", "api", "worker")


if __name__ == "__main__":
    main()

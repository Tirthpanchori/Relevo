"""Development Compose proof: kill a worker, pause recovery, then resume the job.

This deliberately stops/restarts the local worker and scheduler services.
"""

import argparse
import os
import subprocess
import time
from datetime import UTC, datetime
from pathlib import Path
from uuid import UUID, uuid4

import httpx

ROOT = Path(__file__).resolve().parents[1]


def compose(*args: str) -> None:
    subprocess.run(
        ["docker", "compose", *args],
        cwd=ROOT,
        check=True,
        timeout=30,
        capture_output=True,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--recording", type=Path, help="Save sanitized actual database history"
    )
    args = parser.parse_args()
    token = os.environ.get("RELEVO_API_TOKEN")
    if not token:
        raise SystemExit("RELEVO_API_TOKEN must be supplied through the environment")
    with httpx.Client(
        base_url="http://127.0.0.1:8000",
        headers={"Authorization": f"Bearer {token}"},
        timeout=5,
        trust_env=False,
    ) as client:

        def inspect(job_id):
            job = client.get(f"/jobs/{job_id}")
            attempts = client.get(f"/jobs/{job_id}/attempts")
            job.raise_for_status()
            attempts.raise_for_status()
            return job.json(), attempts.json()["attempts"]

        compose("stop", "scheduler")
        try:
            response = client.post(
                "/jobs",
                json={"task_type": "timed_work", "payload": {"duration_seconds": 8}},
                headers={"Idempotency-Key": f"recovery-smoke-{uuid4()}"},
            )
            response.raise_for_status()
            job_id = response.json()["id"]
            deadline = time.monotonic() + 10
            while time.monotonic() < deadline:
                job, attempts = inspect(job_id)
                if job["state"] == "running":
                    break
                assert job["state"] == "pending", (
                    "Job finished before the crash checkpoint"
                )
                time.sleep(0.05)
            else:
                raise SystemExit("Worker did not reach the claimed-job checkpoint")
            first = attempts[0]
            compose("kill", "--signal", "SIGKILL", "worker")
            compose("start", "worker")

            # Only this observation script uses wall time; ownership checks use PostgreSQL time.
            expires_at = datetime.fromisoformat(first["lease_expires_at"])
            deadline = time.monotonic() + 25
            while (expires_at - datetime.now(UTC)).total_seconds() >= -1:
                assert time.monotonic() < deadline, (
                    "Lease did not reach the observation deadline"
                )
                time.sleep(0.1)
            job, attempts = inspect(job_id)
            assert job["state"] == "running" and len(attempts) == 1
            compose("start", "scheduler")

            deadline = time.monotonic() + 35
            while time.monotonic() < deadline:
                job, attempts = inspect(job_id)
                assert job["state"] != "failed", (
                    "Recovery unexpectedly exhausted the job"
                )
                if job["state"] == "succeeded":
                    break
                time.sleep(0.1)
            else:
                raise SystemExit("Restarted scheduler/worker did not complete the job")
            assert [attempt["state"] for attempt in attempts] == [
                "expired",
                "succeeded",
            ]
            assert attempts[1]["fencing_token"] > first["fencing_token"]
            assert attempts[1]["worker_id"] != first["worker_id"]
            stale = client.post(
                f"/internal/attempts/{first['id']}/complete",
                json={
                    "worker_id": first["worker_id"],
                    "fencing_token": first["fencing_token"],
                    "result": {"late": True},
                },
            )
            assert stale.status_code == 409
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
                        UUID(job_id),
                        scenario="worker-crash-recovery",
                        source_file=Path(__file__),
                        source_label="scripts/smoke_recovery.py",
                        observations=[
                            {
                                "checkpoint": "worker_container_killed_after_claim",
                                "signal": "SIGKILL",
                            },
                            {
                                "checkpoint": "job_observed_running_past_lease_with_scheduler_stopped"
                            },
                            {
                                "checkpoint": "scheduler_restarted_and_replacement_completed"
                            },
                            {
                                "checkpoint": "stale_completion_rejected",
                                "status_code": stale.status_code,
                            },
                        ],
                    )
                    write_capture(args.recording, recording)
                finally:
                    engine.dispose()
            print(
                f"Crash/recovery checks passed: job={job_id}, attempts=expired,succeeded, stale=409"
            )
        finally:
            compose("start", "worker", "scheduler")


if __name__ == "__main__":
    main()

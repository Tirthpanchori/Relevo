"""Fixed-backlog benchmark on a guarded, separate database. Never resets development data."""

import argparse
import asyncio
import hashlib
import json
import os
import platform
import re
import statistics
import subprocess
import threading
import time
from datetime import UTC, datetime, timedelta
from importlib.metadata import version
from pathlib import Path

import httpx
from prometheus_client.parser import text_string_to_metric_families
from relevo.api.schemas import SubmitJob
from relevo.client import ClientSettings, RelevoClient
from relevo.engine.serialization import canonical_json
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url

ROOT = Path(__file__).resolve().parents[1]
COMPOSE = ["docker", "compose", "--profile", "benchmark"]
SERVICES = [
    "benchmark-api",
    "benchmark-worker",
    "benchmark-scheduler",
    "postgres-benchmark",
]
WORKLOADS = {
    "short_hash": ("hash_payload", {"message": "x" * 1024}),
    "long_timed": ("timed_work", {"duration_seconds": 0.25}),
}


def command(args, *, env=None):
    result = subprocess.run(
        args,
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )
    if result.returncode:
        # A subprocess error must not dump resolved environment/database credentials.
        raise RuntimeError(
            f"Command failed ({result.returncode}): {' '.join(args[:3])}"
        )
    return result.stdout.strip()


def quantiles(values):
    ordered = sorted(values)
    if not ordered:
        return {"count": 0}
    cuts = (
        statistics.quantiles(ordered, n=100, method="inclusive")
        if len(ordered) > 1
        else ordered * 99
    )
    return {
        "count": len(ordered),
        "mean": statistics.mean(ordered),
        "p50": cuts[49],
        "p95": cuts[94],
        "p99": cuts[98],
        "max": max(ordered),
    }


def metric_samples(raw):
    return {
        (sample.name, tuple(sorted(sample.labels.items()))): sample.value
        for family in text_string_to_metric_families(raw)
        for sample in family.samples
        if sample.name.startswith(("relevo_http_request", "relevo_worker_"))
        and not sample.name.endswith("_created")
    }


def metric_delta(before, after):
    return [
        {
            "name": name,
            "labels": dict(labels),
            "value": value - before.get((name, labels), 0),
        }
        for (name, labels), value in sorted(after.items())
        if value - before.get((name, labels), 0) != 0
    ]


def worker_metrics(workers):
    combined = {}
    code = (
        "import os,urllib.request; "
        "r=urllib.request.Request('http://127.0.0.1:8001/metrics', "
        "headers={'Authorization':'Bearer '+os.environ['RELEVO_API_TOKEN']}); "
        "print(urllib.request.urlopen(r,timeout=3).read().decode())"
    )
    for index in range(1, workers + 1):
        raw = command(
            COMPOSE
            + [
                "exec",
                "-T",
                "--index",
                str(index),
                "benchmark-worker",
                "python",
                "-c",
                code,
            ]
        )
        for key, value in metric_samples(raw).items():
            combined[key] = combined.get(key, 0) + value
    return combined


class ContainerSamples:
    def __init__(self, ids):
        self.rows = []
        self.started = time.monotonic()
        self.process = subprocess.Popen(
            ["docker", "stats", "--format", "{{json .}}", *ids],
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
        )
        self.thread = threading.Thread(target=self.read, daemon=True)
        self.thread.start()

    def read(self):
        for line in self.process.stdout:
            try:
                row = json.loads(re.sub(r"\x1b\[[0-9;]*[A-Za-z]", "", line))
            except ValueError:
                continue
            self.rows.append(
                {"observer_elapsed_seconds": time.monotonic() - self.started, **row}
            )

    def close(self):
        self.process.terminate()
        try:
            self.process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            self.process.kill()
            self.process.wait(timeout=5)
        self.thread.join(timeout=2)
        self.process.stdout.close()


def revision():
    digest = hashlib.sha256()
    files = sorted((ROOT / "backend/src").rglob("*.py")) + [
        ROOT / "backend/uv.lock",
        ROOT / "compose.yaml",
        Path(__file__),
    ]
    for path in files:
        digest.update(
            path.relative_to(ROOT).as_posix().encode()
            + b"\0"
            + path.read_bytes()
            + b"\0"
        )
    return {
        "git_commit": command(["git", "rev-parse", "HEAD"]),
        "source_sha256": digest.hexdigest(),
        "dirty": bool(
            command(["git", "status", "--porcelain", "--untracked-files=no"])
        ),
        "lock_sha256": hashlib.sha256(
            (ROOT / "backend/uv.lock").read_bytes()
        ).hexdigest(),
        "image_id": command(
            [
                "docker",
                "image",
                "inspect",
                "relevo-backend:local",
                "--format",
                "{{.Id}}",
            ]
        ),
    }


def metadata(engine, args):
    with engine.connect() as connection:
        durability = {
            key: connection.execute(text(f"SHOW {key}")).scalar_one()
            for key in ("fsync", "synchronous_commit", "full_page_writes")
        }
        assert set(durability.values()) == {"on"}, "Normal durability is required"
        postgres = connection.execute(text("SHOW server_version")).scalar_one()
        schema = connection.execute(
            text("SELECT version_num FROM alembic_version")
        ).scalar_one()
    docker = json.loads(
        command(
            [
                "docker",
                "info",
                "--format",
                (
                    '{"cpus":{{.NCPU}},"memory_bytes":{{.MemTotal}},"os":"{{.OperatingSystem}}",'
                    '"kernel":"{{.KernelVersion}}","server":"{{.ServerVersion}}"}'
                ),
            ]
        )
    )
    return {
        "format_version": 1,
        "captured_at": datetime.now(UTC).isoformat(),
        "variant": args.variant,
        "revision": revision(),
        "host": {
            "platform": platform.platform(),
            "processor": platform.processor(),
            "docker": docker,
        },
        "dependencies": {
            name: version(name)
            for name in (
                "relevo",
                "fastapi",
                "sqlalchemy",
                "psycopg",
                "httpx",
                "opentelemetry-sdk",
                "prometheus-client",
            )
        },
        "database": {"version": postgres, "schema": schema, "durability": durability},
        "configuration": {
            "jobs_per_run": args.jobs,
            "repeats": args.repeats,
            "worker_counts": args.workers,
            "warmup_jobs": 10,
            "submission_concurrency": 8,
            "common_gate_seconds": 3,
            "observer_poll_seconds": 0.05,
            "monitor_seconds": args.monitor,
            "lease_seconds": 15,
            "heartbeat_seconds": 5,
            "recovery_scan_seconds": 2,
            "task_timeout_seconds": 60,
            "max_attempts": 3,
            "trace_export": False,
            "prometheus_scraping": False,
            "workloads": WORKLOADS,
        },
        "runs": [],
    }


def interrupted_case(engine, workload, workers, repeat):
    with engine.connect() as connection:
        jobs = [
            dict(row)
            for row in connection.execute(
                text("""
            SELECT id,state,attempt_count,event_sequence,created_at,finished_at
            FROM jobs ORDER BY created_at,id
        """)
            ).mappings()
        ]
        attempts = [
            dict(row)
            for row in connection.execute(
                text("""
            SELECT job_id,number,state,fencing_token,started_at,lease_expires_at,finished_at,
                   error->>'code' AS error_code FROM attempts ORDER BY job_id,number
        """)
            ).mappings()
        ]
    return {
        "workload": workload,
        "workers": workers,
        "repeat": repeat,
        "status": "excluded: performance case did not pass its single-attempt accounting guard",
        "jobs": jobs,
        "attempts": attempts,
    }


async def submit_batch(client, task_type, payload, count, key, run_at=None):
    semaphore = asyncio.Semaphore(8)

    async def one(index):
        async with semaphore:
            started = time.perf_counter()
            job = await client.submit(
                SubmitJob(task_type=task_type, payload=payload, run_at=run_at),
                idempotency_key=f"{key}-{index}",
            )
            return job.id, time.perf_counter() - started

    return await asyncio.gather(*(one(index) for index in range(count)))


async def await_terminal(engine, count):
    waits = []
    deadline = time.monotonic() + 120
    while time.monotonic() < deadline:
        with engine.connect() as connection:
            done = connection.execute(
                text("SELECT count(*) FROM jobs WHERE state IN ('succeeded','failed')")
            ).scalar_one()
            lock_count, active = connection.execute(
                text("""
                SELECT count(*) FILTER (WHERE wait_event_type='Lock'),
                       count(*) FILTER (WHERE state='active')
                FROM pg_stat_activity WHERE datname=current_database() AND pid<>pg_backend_pid()
            """)
            ).one()
        waits.append(
            {
                "observer_monotonic": time.monotonic(),
                "lock_waiters": lock_count,
                "active_connections": active,
            }
        )
        if done == count:
            return waits
        await asyncio.sleep(0.05)
    raise TimeoutError("Benchmark jobs did not become terminal in 120 seconds")


async def run_case(engine, client, token, args, workload, workers, repeat):
    command(COMPOSE + ["stop", "benchmark-worker"])
    # This is intentionally destructive only inside the exact guarded benchmark database.
    with engine.begin() as connection:
        connection.execute(
            text(
                "TRUNCATE relevo_demo.effects,relevo_demo.operations,job_events,attempts,jobs CASCADE"
            )
        )
    env = {**os.environ, "RELEVO_BENCHMARK_MONITOR_SECONDS": str(args.monitor)}
    command(
        COMPOSE
        + [
            "up",
            "-d",
            "--no-deps",
            "--scale",
            f"benchmark-worker={workers}",
            "benchmark-worker",
        ],
        env=env,
    )
    await submit_batch(client, "hash_payload", {"warmup": True}, 10, "warmup")
    await await_terminal(engine, 10)
    worker_before = worker_metrics(workers)
    with httpx.Client(
        trust_env=False, headers={"Authorization": f"Bearer {token}"}
    ) as http:
        api_before = metric_samples(http.get("http://127.0.0.1:18000/metrics").text)
    task_type, payload = WORKLOADS[workload]
    ids = command(COMPOSE + ["ps", "-q", *SERVICES]).splitlines()
    sampler = ContainerSamples(ids)
    try:
        with engine.connect() as connection:
            gate = connection.execute(
                text("SELECT clock_timestamp()")
            ).scalar_one() + timedelta(seconds=3)
        submitted = await submit_batch(
            client, task_type, payload, args.jobs, "measured", gate
        )
        with engine.connect() as connection:
            admitted_before_gate = connection.execute(
                text("SELECT clock_timestamp() < :gate"), {"gate": gate}
            ).scalar_one()
        assert admitted_before_gate, (
            "Admission overran the common eligibility gate; discard this run"
        )
        waits = await await_terminal(engine, args.jobs + 10)
    finally:
        sampler.close()
    assert sampler.rows, "No container resource samples; discard this run"
    with httpx.Client(
        trust_env=False, headers={"Authorization": f"Bearer {token}"}
    ) as http:
        api_after = metric_samples(http.get("http://127.0.0.1:18000/metrics").text)
    worker_after = worker_metrics(workers)
    with engine.connect().execution_options(
        isolation_level="REPEATABLE READ"
    ) as connection:
        connection.execute(text("SET TRANSACTION READ ONLY"))
        rows = (
            connection.execute(
                text("""
            SELECT j.id,j.state,j.attempt_count,j.event_sequence,j.result,
                j.created_at,j.finished_at,a.started_at,a.finished_at AS attempt_finished_at,
                a.worker_id,a.state AS attempt_state,a.fencing_token,
                (SELECT count(*) FROM attempts other WHERE other.job_id=j.id) AS attempts,
                (SELECT array_agg(kind ORDER BY sequence) FROM job_events e WHERE e.job_id=j.id) AS history
            FROM jobs j JOIN attempts a ON a.job_id=j.id
            WHERE j.run_at=:gate ORDER BY j.created_at,j.id
        """),
                {"gate": gate},
            )
            .mappings()
            .all()
        )
    expected = (
        {
            "sha256": hashlib.sha256(canonical_json(payload)).hexdigest(),
            "bytes": len(canonical_json(payload)),
        }
        if task_type == "hash_payload"
        else {"worked_seconds": payload["duration_seconds"]}
    )
    assert len(rows) == args.jobs and {row["id"] for row in rows} == {
        item[0] for item in submitted
    }
    raw_jobs = []
    for row in rows:
        assert (
            row["state"] == row["attempt_state"] == "succeeded"
            and row["result"] == expected
        )
        assert row["attempt_count"] == row["attempts"] == row["fencing_token"] == 1
        assert row["event_sequence"] == 3 and row["history"] == [
            "submitted",
            "claimed",
            "succeeded",
        ]
        assert row["started_at"] >= gate and row["finished_at"] >= row["started_at"]
        raw_jobs.append(
            {
                "job_id": str(row["id"]),
                "worker_id": row["worker_id"],
                "created_at": row["created_at"].isoformat(),
                "started_at": row["started_at"].isoformat(),
                "finished_at": row["finished_at"].isoformat(),
                "queue_seconds": (row["started_at"] - gate).total_seconds(),
                "attempt_seconds": (
                    row["attempt_finished_at"] - row["started_at"]
                ).total_seconds(),
                "eligible_to_terminal_seconds": (
                    row["finished_at"] - gate
                ).total_seconds(),
            }
        )
    elapsed = max(row["eligible_to_terminal_seconds"] for row in raw_jobs)
    anchor = waits[0]["observer_monotonic"]
    for wait in waits:
        wait["observer_elapsed_seconds"] = wait.pop("observer_monotonic") - anchor
    inspection_latencies = []
    for job_id, _ in submitted[:10]:
        started = time.perf_counter()
        assert (await client.inspect(job_id)).state == "succeeded"
        inspection_latencies.append(time.perf_counter() - started)
    return {
        "workload": workload,
        "workers": workers,
        "repeat": repeat,
        "eligible_at": gate.isoformat(),
        "correctness": "passed: acknowledged IDs, result, one attempt, fencing, complete ordered history",
        "drain_seconds": elapsed,
        "throughput_jobs_per_second": args.jobs / elapsed,
        "queue_seconds": quantiles([row["queue_seconds"] for row in raw_jobs]),
        "attempt_seconds": quantiles([row["attempt_seconds"] for row in raw_jobs]),
        "eligible_to_terminal_seconds": quantiles(
            [row["eligible_to_terminal_seconds"] for row in raw_jobs]
        ),
        "submission_seconds": quantiles([item[1] for item in submitted]),
        "inspection_seconds": quantiles(inspection_latencies),
        "raw_submission_seconds": [item[1] for item in submitted],
        "raw_inspection_seconds": inspection_latencies,
        "jobs": raw_jobs,
        "api_histogram_delta": metric_delta(api_before, api_after),
        "worker_histogram_delta": metric_delta(worker_before, worker_after),
        "database_samples": waits,
        "container_samples": sampler.rows,
    }


async def main(args):
    source_url = make_url(os.environ["RELEVO_DATABASE_URL"])
    url = source_url.set(host="127.0.0.1", port=15434, database="relevo_benchmark")
    assert (
        url.host == "127.0.0.1"
        and url.port == 15434
        and url.database == "relevo_benchmark"
    )
    engine = create_engine(
        url, connect_args={"connect_timeout": 3, "options": "-c statement_timeout=5000"}
    )
    token = os.environ["RELEVO_API_TOKEN"]
    output = Path(args.output)
    assert not output.exists(), (
        "Use a new artifact name to preserve previous measurements"
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    record = metadata(engine, args)
    settings = ClientSettings(
        api_url="http://127.0.0.1:18000",
        api_token=token,
        submission_attempts=1,
        http_timeout_seconds=10,
    )
    try:
        async with RelevoClient(settings) as client:
            for repeat in range(1, args.repeats + 1):
                for workers in args.workers:
                    for workload in WORKLOADS:
                        try:
                            result = await run_case(
                                engine, client, token, args, workload, workers, repeat
                            )
                        except Exception as exc:
                            record["interrupted_case"] = interrupted_case(
                                engine, workload, workers, repeat
                            )
                            record["failure_type"] = type(exc).__name__
                            output.write_text(
                                json.dumps(record, indent=2, default=str) + "\n",
                                encoding="utf-8",
                            )
                            raise
                        record["runs"].append(result)
                        output.write_text(
                            json.dumps(record, indent=2) + "\n", encoding="utf-8"
                        )
                        print(
                            f"{args.variant}: {workload} workers={workers} repeat={repeat}: "
                            f"{result['throughput_jobs_per_second']:.3f} jobs/s, accounting passed",
                            flush=True,
                        )
    finally:
        command(
            COMPOSE
            + [
                "stop",
                "benchmark-worker",
                "benchmark-scheduler",
                "benchmark-api",
                "postgres-benchmark",
            ]
        )
        engine.dispose()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--variant", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--jobs", type=int, default=30)
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument("--workers", nargs="+", type=int, default=[1, 3, 5])
    parser.add_argument("--monitor", type=float, default=0.05)
    args = parser.parse_args()
    assert (
        10 <= args.jobs <= 1000
        and 1 <= args.repeats <= 5
        and set(args.workers) <= {1, 3, 5}
    )
    assert 0.001 <= args.monitor <= 1
    asyncio.run(main(args))

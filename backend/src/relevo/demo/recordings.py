"""Sanitized database snapshots with actual capture/source/configuration metadata."""

import hashlib
import json
import platform
import subprocess
from datetime import UTC, datetime
from pathlib import Path
from uuid import UUID

from sqlalchemy import Engine, text

from relevo.config import Settings


def _json_value(value):
    if isinstance(value, (datetime, UUID)):
        return value.isoformat() if isinstance(value, datetime) else str(value)
    raise TypeError("Unsupported recording value")


def capture_job(
    engine: Engine,
    settings: Settings,
    job_id: UUID,
    *,
    scenario: str,
    source_file: Path,
    source_label: str,
    observations: list[dict],
) -> dict:
    backend = Path.cwd() / "backend" if (Path.cwd() / "backend").is_dir() else Path.cwd()
    digest = hashlib.sha256()
    paths = sorted([*backend.glob("src/**/*.py"), *backend.glob("tests/**/*.py")])
    paths += [backend / "pyproject.toml", backend / "uv.lock"]
    for path in paths:
        if path.is_file():
            digest.update(path.relative_to(backend).as_posix().encode() + b"\0")
            digest.update(path.read_bytes() + b"\0")
    try:
        revision = subprocess.run(
            ["git", "rev-parse", "HEAD"], capture_output=True, text=True, timeout=3, check=False
        )
        commit = revision.stdout.strip() if revision.returncode == 0 else None
    except (OSError, subprocess.TimeoutExpired):
        commit = None
    with engine.connect().execution_options(isolation_level="REPEATABLE READ") as connection:
        connection.execute(text("SET TRANSACTION READ ONLY"))
        job = dict(
            connection.execute(
                text("""
            SELECT id, task_type, state, attempt_count, max_attempts, event_sequence,
                   current_attempt_id, created_at, updated_at, finished_at, available_at
            FROM jobs WHERE id=:id
        """),
                {"id": job_id},
            )
            .mappings()
            .one()
        )
        attempts = [
            dict(row)
            for row in connection.execute(
                text("""
            SELECT id, number, fencing_token, worker_id, state, started_at, lease_expires_at,
                   finished_at, error->>'code' AS error_code
            FROM attempts WHERE job_id=:id ORDER BY number
        """),
                {"id": job_id},
            ).mappings()
        ]
        events = []
        allowed = {
            "state",
            "worker_id",
            "fencing_token",
            "attempt_number",
            "retry_scheduled",
            "available_at",
            "task_type",
            "queue_delay_seconds",
            "attempt_duration_seconds",
        }
        for row in connection.execute(
            text("""
            SELECT sequence, attempt_id, kind, occurred_at, data
            FROM job_events WHERE job_id=:id ORDER BY sequence
        """),
            {"id": job_id},
        ).mappings():
            events.append(
                {
                    **row,
                    "data": {key: value for key, value in row["data"].items() if key in allowed},
                }
            )
        effects = [
            dict(row)
            for row in connection.execute(
                text("""
            SELECT id, job_id, attempt_id, units, (operation_key IS NOT NULL) AS protected,
                   created_at FROM relevo_demo.effects WHERE job_id=:id ORDER BY created_at, id
        """),
                {"id": job_id},
            ).mappings()
        ]
        schema = connection.execute(text("SELECT version_num FROM alembic_version")).scalar_one()
        postgres = connection.execute(text("SHOW server_version")).scalar_one()
    record = {
        "format_version": 1,
        "scenario": scenario,
        "captured_at": datetime.now(UTC),
        "source": {
            "path": source_label,
            "sha256": hashlib.sha256(source_file.read_bytes()).hexdigest(),
        },
        "revision": {"git_commit": commit, "backend_tree_sha256": digest.hexdigest()},
        "environment": {
            "python": platform.python_version(),
            "postgres": postgres,
            "schema_version": schema,
        },
        "configuration": {
            key: getattr(settings, key)
            for key in (
                "lease_seconds",
                "heartbeat_seconds",
                "recovery_scan_seconds",
                "recovery_batch_size",
                "max_attempts",
                "retry_base_seconds",
                "retry_max_seconds",
                "task_timeout_seconds",
            )
        },
        "observations": observations,
        "job": job,
        "attempts": attempts,
        "events": events,
        "business_effects": effects,
    }
    # No token, DSN, idempotency key, business key, payload/result, or free-form error message.
    return json.loads(json.dumps(record, default=_json_value, allow_nan=False))


def write_capture(path: Path, recording: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".tmp")
    temporary.write_text(
        json.dumps(recording, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    temporary.replace(path)

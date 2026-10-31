"""Local Compose backups and an isolated restore drill; never restore over development."""

import argparse
import hashlib
import json
import subprocess
import uuid
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def run(service, *args, data=None):
    result = subprocess.run(
        ["docker", "compose", "exec", "-T", service, *args],
        cwd=ROOT,
        input=data,
        capture_output=True,
        timeout=120,
        check=False,
    )
    if result.returncode:
        raise RuntimeError("Database command failed; inspect local Docker logs")
    return result.stdout


def sql(service, database, statement):
    return (
        run(
            service,
            "psql",
            "-U",
            "relevo",
            "-d",
            database,
            "-At",
            "-v",
            "ON_ERROR_STOP=1",
            "-c",
            statement,
        )
        .decode()
        .strip()
    )


def snapshot(service, database):
    # Full durable rows, not counts alone: catches lost/changed identities and history.
    result = {}
    for table in ("jobs", "attempts", "job_events", "alembic_version"):
        result[table] = sql(
            service,
            database,
            f"SELECT coalesce(jsonb_agg(to_jsonb(t) ORDER BY to_jsonb(t)::text), '[]') "
            f"FROM public.{table} t",
        )
    return result


def backup(output):
    output = Path(output).resolve()
    if output.exists():
        raise ValueError("Backup already exists; choose a new output filename")
    output.parent.mkdir(parents=True, exist_ok=True)
    data = run(
        "postgres", "pg_dump", "-U", "relevo", "-d", "relevo", "-Fc", "--no-owner"
    )
    with output.open("xb") as stream:
        stream.write(data)
    print(
        f"Backup saved: {output.name} ({len(data)} bytes). Keep it private and off-site."
    )


def restore_drill():
    # Separate databases on the ephemeral test service, no development data copied or changed.
    prefix = "relevo_restore_" + uuid.uuid4().hex[:12]
    source, target = prefix + "_source_test", prefix + "_target_test"
    created = []
    try:
        for name in (source, target):
            run("postgres-test", "createdb", "-U", "relevo", name)
            created.append(name)
        schema = run(
            "postgres-test",
            "pg_dump",
            "-U",
            "relevo",
            "-d",
            "relevo_test",
            "--schema-only",
            "--no-owner",
            "--no-privileges",
        )
        run(
            "postgres-test",
            "psql",
            "-U",
            "relevo",
            "-d",
            source,
            "-v",
            "ON_ERROR_STOP=1",
            data=schema,
        )
        # Synthetic pending and completed tasks exercise real migrated FK constraints.
        sql(
            "postgres-test",
            source,
            """
          INSERT INTO alembic_version(version_num) VALUES ('0003');
          INSERT INTO jobs(id,idempotency_key,request_fingerprint,task_type,payload,state,
             available_at,created_at,updated_at,finished_at,max_attempts,attempt_count,
             fencing_token,event_sequence,result)
          VALUES ('00000000-0000-0000-0000-000000000001','restore-pending',repeat('a',64),
             'hash_payload','{}','pending',now(),now(),now(),NULL,3,0,0,1,NULL),
             ('00000000-0000-0000-0000-000000000002','restore-completed',repeat('b',64),
             'hash_payload','{}','succeeded',now(),now(),now(),now(),3,1,1,3,'{"restored":true}');
          INSERT INTO attempts(id,job_id,number,fencing_token,worker_id,state,started_at,
             lease_expires_at,finished_at,result)
          VALUES ('00000000-0000-0000-0000-000000000003',
             '00000000-0000-0000-0000-000000000002',1,1,'restore-worker','succeeded',
             now(),now()+interval '15 seconds',now(),'{"restored":true}');
          INSERT INTO job_events(job_id,sequence,attempt_id,kind,occurred_at,data)
          VALUES ('00000000-0000-0000-0000-000000000001',1,NULL,'submitted',now(),'{"state":"pending"}'),
             ('00000000-0000-0000-0000-000000000002',1,NULL,'submitted',now(),'{"state":"pending"}'),
             ('00000000-0000-0000-0000-000000000002',2,'00000000-0000-0000-0000-000000000003','claimed',now(),'{"state":"running"}'),
             ('00000000-0000-0000-0000-000000000002',3,'00000000-0000-0000-0000-000000000003','succeeded',now(),'{"state":"succeeded"}');
        """,
        )
        before = snapshot("postgres-test", source)
        archive = run(
            "postgres-test",
            "pg_dump",
            "-U",
            "relevo",
            "-d",
            source,
            "-Fc",
            "--no-owner",
        )
        run(
            "postgres-test",
            "pg_restore",
            "-U",
            "relevo",
            "-d",
            target,
            "--no-owner",
            "--no-privileges",
            "--exit-on-error",
            data=archive,
        )
        after = snapshot("postgres-test", target)
        if before != after:
            raise RuntimeError("Restored rows differ")
        record = {
            "verified_at": datetime.now(UTC).isoformat(),
            "archive_sha256": hashlib.sha256(archive).hexdigest(),
            "tables_equal": list(before),
            "schema_restored": True,
            "fixture": "synthetic pending/completed jobs, attempt and four events",
            "rows": {k: len(json.loads(v)) for k, v in before.items()},
            "development_touched": False,
        }
        path = ROOT / "artifacts/verification/backup-restore.json"
        path.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
        print("Isolated schema/data restore matched the source. Evidence recorded.")
    finally:
        for name in reversed(created):
            run("postgres-test", "dropdb", "-U", "relevo", "--force", name)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("backup").add_argument("--output", required=True)
    sub.add_parser("restore-drill")
    args = parser.parse_args()
    backup(args.output) if args.command == "backup" else restore_drill()


if __name__ == "__main__":
    main()

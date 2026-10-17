"""Bounded, replay-safe expiry scans following the engine's job-before-attempt locks."""

from collections.abc import Callable
from dataclasses import dataclass
from datetime import timedelta
from uuid import UUID

from sqlalchemy import Engine, bindparam, text
from sqlalchemy.dialects.postgresql import JSONB

from relevo.config import Settings
from relevo.engine.ownership import append_event, database_now, lock_attempt
from relevo.engine.retries import retry_delay_seconds
from relevo.observability import log_event, observed


@dataclass(frozen=True, slots=True)
class RecoveredAttempt:
    job_id: UUID
    attempt_id: UUID
    fencing_token: int
    state: str


@observed("recovery")
def recover_expired(
    engine: Engine,
    settings: Settings,
    *,
    random_source: Callable[[], float] | None = None,
) -> list[RecoveredAttempt]:
    recovered = []
    with engine.begin() as connection:
        candidates = (
            connection.execute(
                text("""
                SELECT j.id, j.current_attempt_id
                FROM attempts AS a JOIN jobs AS j
                  ON j.current_attempt_id=a.id AND j.id=a.job_id
                WHERE j.state='running' AND a.state='running'
                  AND a.lease_expires_at <= statement_timestamp()
                ORDER BY a.lease_expires_at, j.id
                LIMIT :batch_size FOR UPDATE OF j SKIP LOCKED
            """),
                {"batch_size": settings.recovery_batch_size},
            )
            .mappings()
            .all()
        )
        for candidate in candidates:
            # Re-read after locks: the candidate join is only a discovery snapshot.
            job, attempt = lock_attempt(connection, candidate["current_attempt_id"])
            now = database_now(connection)
            if (
                job["state"] != "running"
                or attempt["state"] != "running"
                or job["current_attempt_id"] != attempt["id"]
                or job["fencing_token"] != attempt["fencing_token"]
                or attempt["lease_expires_at"] > now
            ):
                continue
            error = {"code": "lease_expired", "message": "Attempt lease expired before an outcome"}
            changed = connection.execute(
                text("""
                    UPDATE attempts SET state='expired', finished_at=:now, error=:error
                    WHERE id=:id AND state='running' AND fencing_token=:token
                      AND lease_expires_at <= clock_timestamp()
                    RETURNING id
                """).bindparams(bindparam("error", type_=JSONB)),
                {
                    "id": attempt["id"],
                    "token": attempt["fencing_token"],
                    "now": now,
                    "error": error,
                },
            ).scalar_one_or_none()
            if changed is None:
                # A backwards database-clock correction can make an expiry ineligible again.
                continue
            retry = job["attempt_count"] < job["max_attempts"]
            state = "pending" if retry else "failed"
            available_at = job["available_at"]
            if retry:
                delay_args = {} if random_source is None else {"random_source": random_source}
                available_at = now + timedelta(
                    seconds=retry_delay_seconds(attempt["number"], settings, **delay_args)
                )
            sequence = connection.execute(
                text("""
                    UPDATE jobs SET state=:state, current_attempt_id=NULL, updated_at=:now,
                        finished_at=:finished_at, available_at=:available_at,
                        result=NULL, error=:error, event_sequence=event_sequence+1
                    WHERE id=:id AND state='running' AND current_attempt_id=:attempt_id
                      AND fencing_token=:token
                    RETURNING event_sequence
                """).bindparams(bindparam("error", type_=JSONB)),
                {
                    "id": job["id"],
                    "attempt_id": attempt["id"],
                    "token": attempt["fencing_token"],
                    "state": state,
                    "now": now,
                    "finished_at": None if retry else now,
                    "available_at": available_at,
                    "error": error,
                },
            ).scalar_one()
            append_event(
                connection,
                job["id"],
                sequence,
                attempt["id"],
                "expired",
                now,
                {
                    "state": state,
                    "retry_scheduled": retry,
                    "worker_id": attempt["worker_id"],
                    "fencing_token": attempt["fencing_token"],
                    "available_at": available_at.isoformat(),
                    "attempt_duration_seconds": max(
                        0, (now - attempt["started_at"]).total_seconds()
                    ),
                },
            )
            recovered.append(
                RecoveredAttempt(job["id"], attempt["id"], attempt["fencing_token"], state)
            )
    # No observation escapes until the entire batch commits.
    for item in recovered:
        log_event(
            "transition_committed",
            transition="expired",
            job_id=item.job_id,
            attempt_id=item.attempt_id,
            fencing_token=item.fencing_token,
            state=item.state,
        )
    return recovered

"""Short, explicit SQL transactions for ownership. Never execute handlers here.

All mutating operations lock the job before the attempt and sample current DB time
after those locks. A report replay acknowledges history; it cannot revive ownership.
"""

from collections.abc import Callable, Mapping
from datetime import datetime, timedelta
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import Connection, Engine, bindparam, text
from sqlalchemy.dialects.postgresql import JSONB

from relevo.api.schemas import (
    ClaimResponse,
    CompleteRequest,
    FailRequest,
    HeartbeatResponse,
    OutcomeResponse,
    Ownership,
)
from relevo.config import Settings
from relevo.engine.errors import AttemptNotFound, OwnershipConflict, SizeLimitExceeded
from relevo.engine.retries import retry_delay_seconds
from relevo.engine.serialization import canonical_json, fingerprint
from relevo.observability import log_event, observed


def database_now(connection: Connection) -> datetime:
    return connection.execute(text("SELECT clock_timestamp()")).scalar_one()


def append_event(
    connection: Connection,
    job_id: UUID,
    sequence: int,
    attempt_id: UUID,
    kind: str,
    occurred_at: datetime,
    data: dict[str, Any],
) -> None:
    connection.execute(
        text("""
            INSERT INTO job_events (job_id, sequence, attempt_id, kind, occurred_at, data)
            VALUES (:job_id, :sequence, :attempt_id, :kind, :occurred_at, :data)
        """).bindparams(bindparam("data", type_=JSONB)),
        dict(
            job_id=job_id,
            sequence=sequence,
            attempt_id=attempt_id,
            kind=kind,
            occurred_at=occurred_at,
            data=data,
        ),
    )


@observed("claim")
def claim_job(engine: Engine, settings: Settings, worker_id: str) -> ClaimResponse | None:
    with engine.begin() as connection:
        job = (
            connection.execute(
                text("""
            SELECT * FROM jobs
            WHERE state = 'pending' AND available_at <= statement_timestamp()
              AND attempt_count < max_attempts
            ORDER BY available_at, created_at, id
            LIMIT 1 FOR UPDATE SKIP LOCKED
        """)
            )
            .mappings()
            .one_or_none()
        )
        if job is None:
            return None
        now = database_now(connection)
        if job["available_at"] > now:
            # A backwards database-clock correction must not make delayed work start early.
            return None
        attempt_id = uuid4()
        number = job["attempt_count"] + 1
        token = job["fencing_token"] + 1
        expires_at = now + timedelta(seconds=settings.lease_seconds)
        connection.execute(
            text("""
            INSERT INTO attempts
                (id, job_id, number, fencing_token, worker_id, state, started_at, lease_expires_at)
            VALUES (:id, :job_id, :number, :token, :worker_id, 'running', :now, :expires_at)
        """),
            dict(
                id=attempt_id,
                job_id=job["id"],
                number=number,
                token=token,
                worker_id=worker_id,
                now=now,
                expires_at=expires_at,
            ),
        )
        sequence = connection.execute(
            text("""
            UPDATE jobs SET state='running', current_attempt_id=:attempt_id,
                attempt_count=:number, fencing_token=:token, updated_at=:now,
                event_sequence=event_sequence+1
            WHERE id=:job_id AND state='pending' AND attempt_count=:previous_count
            RETURNING event_sequence
        """),
            dict(
                attempt_id=attempt_id,
                number=number,
                token=token,
                now=now,
                job_id=job["id"],
                previous_count=job["attempt_count"],
            ),
        ).scalar_one()
        append_event(
            connection,
            job["id"],
            sequence,
            attempt_id,
            "claimed",
            now,
            {
                "state": "running",
                "worker_id": worker_id,
                "fencing_token": token,
                "attempt_number": number,
                "queue_delay_seconds": max(0, (now - job["available_at"]).total_seconds()),
            },
        )
        response = ClaimResponse(
            job_id=job["id"],
            attempt_id=attempt_id,
            attempt_number=number,
            fencing_token=token,
            lease_expires_at=expires_at,
            task_type=job["task_type"],
            payload=job["payload"],
            task_timeout_seconds=settings.task_timeout_seconds,
            lease_seconds=settings.lease_seconds,
            max_result_bytes=settings.max_result_bytes,
        )
    log_event(
        "transition_committed",
        transition="claimed",
        job_id=response.job_id,
        attempt_id=response.attempt_id,
        worker_id=worker_id,
        fencing_token=response.fencing_token,
        state="running",
        sequence=sequence,
    )
    return response


def lock_attempt(
    connection: Connection,
    attempt_id: UUID,
) -> tuple[Mapping[str, Any], Mapping[str, Any]]:
    # This unlocked lookup identifies the parent only. job_id is immutable; v1 has no deletion.
    job_id = connection.execute(
        text("SELECT job_id FROM attempts WHERE id=:id"),
        {"id": attempt_id},
    ).scalar_one_or_none()
    if job_id is None:
        raise AttemptNotFound("Attempt does not exist")
    job = (
        connection.execute(
            text("SELECT * FROM jobs WHERE id=:id FOR UPDATE"),
            {"id": job_id},
        )
        .mappings()
        .one()
    )
    attempt = (
        connection.execute(
            text("SELECT * FROM attempts WHERE id=:id FOR UPDATE"),
            {"id": attempt_id},
        )
        .mappings()
        .one()
    )
    return job, attempt


def check_identity(attempt: Mapping[str, Any], ownership: Ownership) -> None:
    if (
        attempt["worker_id"] != ownership.worker_id
        or attempt["fencing_token"] != ownership.fencing_token
    ):
        raise OwnershipConflict("The attempt identity does not match this assignment")


def check_current_owner(
    job: Mapping[str, Any],
    attempt: Mapping[str, Any],
    ownership: Ownership,
    now: datetime,
) -> None:
    check_identity(attempt, ownership)
    if (
        job["state"] != "running"
        or attempt["state"] != "running"
        or job["current_attempt_id"] != attempt["id"]
        or job["fencing_token"] != ownership.fencing_token
        or attempt["lease_expires_at"] <= now
    ):
        raise OwnershipConflict("The attempt no longer holds the current unexpired lease")


@observed("heartbeat")
def renew_lease(
    engine: Engine,
    settings: Settings,
    attempt_id: UUID,
    ownership: Ownership,
) -> HeartbeatResponse:
    with engine.begin() as connection:
        job, attempt = lock_attempt(connection, attempt_id)
        now = database_now(connection)
        check_current_owner(job, attempt, ownership, now)
        expires_at = connection.execute(
            text("""
            UPDATE attempts SET lease_expires_at=GREATEST(lease_expires_at, :expires_at)
            WHERE id=:id AND state='running' AND fencing_token=:token AND worker_id=:worker_id
              AND lease_expires_at > clock_timestamp()
            RETURNING lease_expires_at
        """),
            dict(
                id=attempt_id,
                token=ownership.fencing_token,
                worker_id=ownership.worker_id,
                expires_at=now + timedelta(seconds=settings.lease_seconds),
            ),
        ).scalar_one_or_none()
        if expires_at is None:
            raise OwnershipConflict("The lease expired before renewal")
        connection.execute(
            text("UPDATE jobs SET updated_at=:now WHERE id=:id"),
            {"now": now, "id": job["id"]},
        )
        response = HeartbeatResponse(
            attempt_id=attempt_id,
            lease_expires_at=expires_at,
            lease_seconds=settings.lease_seconds,
        )
    return response


@observed("report")
def report_outcome(
    engine: Engine,
    settings: Settings,
    attempt_id: UUID,
    report: CompleteRequest | FailRequest,
    *,
    random_source: Callable[[], float] | None = None,
) -> OutcomeResponse:
    is_success = isinstance(report, CompleteRequest)
    kind = "succeeded" if is_success else "failed"
    report_fingerprint = fingerprint({"kind": kind, **report.model_dump(mode="json")})
    with engine.begin() as connection:
        job, attempt = lock_attempt(connection, attempt_id)
        check_identity(attempt, report)
        if attempt["state"] != "running":
            if attempt["report_fingerprint"] == report_fingerprint:
                # Historical acknowledgment remains valid after expiry or reassignment.
                return OutcomeResponse.model_validate(attempt["report_response"])
            raise OwnershipConflict("A different outcome or expiry was already recorded")
        now = database_now(connection)
        check_current_owner(job, attempt, report, now)
        result = report.result if is_success else None
        error = None if is_success else report.error.model_dump(mode="json")
        if is_success and len(canonical_json(result)) > settings.max_result_bytes:
            raise SizeLimitExceeded("Result exceeds the configured serialized UTF-8 byte limit")
        retry = not is_success and report.retryable and job["attempt_count"] < job["max_attempts"]
        available_at = job["available_at"]
        if retry:
            delay_args = {} if random_source is None else {"random_source": random_source}
            available_at = now + timedelta(
                seconds=retry_delay_seconds(attempt["number"], settings, **delay_args),
            )
        state = "succeeded" if is_success else ("pending" if retry else "failed")
        response = OutcomeResponse(
            job_id=job["id"],
            attempt_id=attempt_id,
            state=state,
            available_at=available_at,
        )
        changed = connection.execute(
            text("""
            UPDATE attempts SET state=:state, finished_at=:now, result=:result, error=:error,
                report_fingerprint=:fingerprint, report_response=:response
            WHERE id=:id AND state='running' AND fencing_token=:token AND worker_id=:worker_id
              AND lease_expires_at > clock_timestamp()
            RETURNING id
        """).bindparams(
                bindparam("result", type_=JSONB(none_as_null=True)),
                bindparam("error", type_=JSONB(none_as_null=True)),
                bindparam("response", type_=JSONB),
            ),
            dict(
                state=kind,
                now=now,
                result=result,
                error=error,
                fingerprint=report_fingerprint,
                response=response.model_dump(mode="json"),
                id=attempt_id,
                token=report.fencing_token,
                worker_id=report.worker_id,
            ),
        ).scalar_one_or_none()
        if changed is None:
            raise OwnershipConflict("The lease expired before the outcome was recorded")
        sequence = connection.execute(
            text("""
            UPDATE jobs SET state=:state, current_attempt_id=NULL, updated_at=:now,
                finished_at=:finished_at, available_at=:available_at, result=:result, error=:error,
                event_sequence=event_sequence+1
            WHERE id=:id AND current_attempt_id=:attempt_id AND fencing_token=:token
            RETURNING event_sequence
        """).bindparams(
                bindparam("result", type_=JSONB(none_as_null=True)),
                bindparam("error", type_=JSONB(none_as_null=True)),
            ),
            dict(
                state=state,
                now=now,
                finished_at=None if retry else now,
                available_at=available_at,
                result=result,
                error=error,
                id=job["id"],
                attempt_id=attempt_id,
                token=report.fencing_token,
            ),
        ).scalar_one()
        append_event(
            connection,
            job["id"],
            sequence,
            attempt_id,
            kind,
            now,
            {
                "state": state,
                "retry_scheduled": retry,
                "fencing_token": report.fencing_token,
                "available_at": available_at.isoformat(),
                "attempt_duration_seconds": max(0, (now - attempt["started_at"]).total_seconds()),
            },
        )
    log_event(
        "transition_committed",
        transition=kind,
        job_id=response.job_id,
        attempt_id=attempt_id,
        worker_id=report.worker_id,
        fencing_token=report.fencing_token,
        state=response.state,
        sequence=sequence,
    )
    return response

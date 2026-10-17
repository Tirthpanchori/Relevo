"""Durable submission: a unique key resolves concurrency and lost-response ambiguity."""

from uuid import UUID, uuid4

from sqlalchemy import Engine, select, text
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from relevo.api.schemas import AttemptHistory, AttemptView, JobView, SubmitJob
from relevo.config import Settings
from relevo.db.models import Attempt, Job, JobEvent
from relevo.engine.errors import IdempotencyConflict, JobNotFound, SizeLimitExceeded
from relevo.engine.serialization import canonical_json, fingerprint
from relevo.observability import log_event, observed


@observed("submit")
def submit_job(
    engine: Engine,
    settings: Settings,
    request: SubmitJob,
    idempotency_key: str,
) -> tuple[JobView, bool]:
    oversized = len(canonical_json(request.payload)) > settings.max_payload_bytes
    # This is the original normalized request, not the effective server-generated schedule.
    request_fingerprint = fingerprint(request.model_dump(mode="json"))
    with Session(engine) as session, session.begin():
        if oversized:
            # A lower admission limit must not invalidate an already-committed acknowledgment.
            existing = session.scalar(select(Job).where(Job.idempotency_key == idempotency_key))
            if existing is None:
                raise SizeLimitExceeded(
                    "Payload exceeds the configured serialized UTF-8 byte limit"
                )
            if existing.request_fingerprint != request_fingerprint:
                raise IdempotencyConflict("The idempotency key is already bound to different work")
            return JobView.model_validate(existing), False
        now = session.execute(text("SELECT clock_timestamp()")).scalar_one()
        new_id = uuid4()
        inserted_id = session.execute(
            insert(Job)
            .values(
                id=new_id,
                idempotency_key=idempotency_key,
                request_fingerprint=request_fingerprint,
                task_type=request.task_type,
                payload=request.payload,
                run_at=request.run_at,
                state="pending",
                available_at=request.run_at or now,
                created_at=now,
                updated_at=now,
                max_attempts=settings.max_attempts,
                attempt_count=0,
                fencing_token=0,
                event_sequence=1,
            )
            .on_conflict_do_nothing(index_elements=[Job.idempotency_key])
            .returning(Job.id)
        ).scalar_one_or_none()
        # READ COMMITTED supplies a fresh snapshot after a concurrent inserter commits.
        job = session.execute(
            select(Job).where(Job.idempotency_key == idempotency_key)
        ).scalar_one()
        if job.request_fingerprint != request_fingerprint:
            raise IdempotencyConflict("The idempotency key is already bound to different work")
        created = inserted_id is not None
        if created:
            session.add(
                JobEvent(
                    job_id=job.id,
                    sequence=1,
                    kind="submitted",
                    occurred_at=now,
                    data={"state": "pending"},
                )
            )
        view = JobView.model_validate(job)
    # Exiting session.begin() commits; no successful view escapes a failed commit.
    if created:
        log_event("transition_committed", transition="submitted", job_id=view.id, state=view.state)
    return view, created


@observed("inspect")
def get_job(engine: Engine, job_id: UUID) -> JobView:
    with Session(engine) as session:
        job = session.get(Job, job_id)
        if job is None:
            raise JobNotFound("Job does not exist")
        return JobView.model_validate(job)


@observed("attempts")
def get_attempts(engine: Engine, job_id: UUID) -> AttemptHistory:
    with Session(engine) as session:
        if session.get(Job, job_id) is None:
            raise JobNotFound("Job does not exist")
        attempts = session.scalars(
            select(Attempt).where(Attempt.job_id == job_id).order_by(Attempt.number)
        ).all()
        return AttemptHistory(
            job_id=job_id,
            attempts=[AttemptView.model_validate(attempt) for attempt in attempts],
        )

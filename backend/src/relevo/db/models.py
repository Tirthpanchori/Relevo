"""Persistent state; Alembic, rather than application startup, owns schema changes."""

from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    Integer,
    String,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Job(Base):
    __tablename__ = "jobs"
    __table_args__ = (
        CheckConstraint(
            "state IN ('pending','running','succeeded','failed')", name="ck_jobs_state"
        ),
        CheckConstraint("max_attempts >= 1", name="ck_jobs_max_attempts"),
        CheckConstraint(
            "attempt_count >= 0 AND attempt_count <= max_attempts", name="ck_jobs_attempt_count"
        ),
        CheckConstraint("fencing_token >= 0", name="ck_jobs_token"),
        CheckConstraint("event_sequence >= 1", name="ck_jobs_event_sequence"),
        CheckConstraint(
            "(state = 'running') = (current_attempt_id IS NOT NULL)", name="ck_jobs_ownership"
        ),
        CheckConstraint(
            "(state IN ('succeeded','failed')) = (finished_at IS NOT NULL)", name="ck_jobs_terminal"
        ),
        ForeignKeyConstraint(
            ["id", "current_attempt_id"],
            ["attempts.job_id", "attempts.id"],
            name="fk_jobs_current_attempt",
            use_alter=True,
            deferrable=True,
            initially="DEFERRED",
        ),
        Index(
            "ix_jobs_available",
            "available_at",
            "created_at",
            "id",
            postgresql_where=text("state = 'pending'"),
        ),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True)
    idempotency_key: Mapped[str] = mapped_column(String(200), unique=True)
    request_fingerprint: Mapped[str] = mapped_column(String(64))
    task_type: Mapped[str] = mapped_column(String(80))
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB)
    run_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    state: Mapped[str] = mapped_column(String(16))
    available_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    max_attempts: Mapped[int] = mapped_column(Integer)
    attempt_count: Mapped[int] = mapped_column(Integer, default=0)
    fencing_token: Mapped[int] = mapped_column(BigInteger, default=0)
    event_sequence: Mapped[int] = mapped_column(BigInteger, default=1)
    current_attempt_id: Mapped[UUID | None]
    result: Mapped[Any | None] = mapped_column(JSONB(none_as_null=True), nullable=True)
    error: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)


class Attempt(Base):
    __tablename__ = "attempts"
    __table_args__ = (
        UniqueConstraint("job_id", "id", name="uq_attempts_job_id_id"),
        UniqueConstraint("job_id", "number", name="uq_attempts_number"),
        UniqueConstraint("job_id", "fencing_token", name="uq_attempts_token"),
        CheckConstraint("number >= 1 AND fencing_token >= 1", name="ck_attempts_numbers"),
        CheckConstraint(
            "state IN ('running','succeeded','failed','expired')", name="ck_attempts_state"
        ),
        CheckConstraint("(state = 'running') = (finished_at IS NULL)", name="ck_attempts_terminal"),
        Index(
            "ix_attempts_expired", "lease_expires_at", postgresql_where=text("state = 'running'")
        ),
        Index(
            "uq_attempts_running_job",
            "job_id",
            unique=True,
            postgresql_where=text("state = 'running'"),
        ),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True)
    job_id: Mapped[UUID] = mapped_column(ForeignKey("jobs.id", ondelete="RESTRICT"))
    number: Mapped[int] = mapped_column(Integer)
    fencing_token: Mapped[int] = mapped_column(BigInteger)
    worker_id: Mapped[str] = mapped_column(String(200))
    state: Mapped[str] = mapped_column(String(16))
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    lease_expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    result: Mapped[Any | None] = mapped_column(JSONB(none_as_null=True), nullable=True)
    error: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    report_fingerprint: Mapped[str | None] = mapped_column(String(64))
    report_response: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)


class JobEvent(Base):
    __tablename__ = "job_events"
    __table_args__ = (
        CheckConstraint("sequence >= 1", name="ck_job_events_sequence"),
        ForeignKeyConstraint(
            ["job_id", "attempt_id"],
            ["attempts.job_id", "attempts.id"],
            name="fk_job_events_attempt",
            ondelete="RESTRICT",
        ),
    )

    job_id: Mapped[UUID] = mapped_column(
        ForeignKey("jobs.id", ondelete="RESTRICT"), primary_key=True
    )
    sequence: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    attempt_id: Mapped[UUID | None]
    kind: Mapped[str] = mapped_column(String(40))
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    data: Mapped[dict[str, Any]] = mapped_column(JSONB)

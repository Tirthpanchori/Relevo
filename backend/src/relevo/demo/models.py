"""A separate schema/store boundary; no foreign keys into executor-owned state."""

from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class DemoBase(DeclarativeBase):
    pass


class BusinessOperation(DemoBase):
    __tablename__ = "operations"
    __table_args__ = {"schema": "relevo_demo"}

    business_key: Mapped[str] = mapped_column(String(200), primary_key=True)
    request_fingerprint: Mapped[str] = mapped_column(String(64))
    result: Mapped[dict[str, Any]] = mapped_column(JSONB)


class BusinessEffect(DemoBase):
    __tablename__ = "effects"
    __table_args__ = (
        CheckConstraint("units >= 1 AND units <= 1000000", name="ck_demo_effect_units"),
        CheckConstraint(
            "operation_key IS NULL OR operation_key=business_key", name="ck_demo_effect_key"
        ),
        {"schema": "relevo_demo"},
    )

    id: Mapped[UUID] = mapped_column(primary_key=True)
    business_key: Mapped[str] = mapped_column(String(200))
    operation_key: Mapped[str | None] = mapped_column(
        ForeignKey("relevo_demo.operations.business_key"), unique=True
    )
    job_id: Mapped[UUID]
    attempt_id: Mapped[UUID]
    units: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))

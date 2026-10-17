"""A business transaction, deliberately independent of executor completion transactions."""

import re
from uuid import UUID, uuid4

from sqlalchemy import Engine, bindparam, text
from sqlalchemy.dialects.postgresql import JSONB

from relevo.engine.serialization import fingerprint


class BusinessConflict(ValueError):
    pass


def commit_effect(
    engine: Engine,
    *,
    business_key: str,
    units: int,
    job_id: UUID,
    attempt_id: UUID,
    protected: bool,
) -> dict:
    if not re.fullmatch(r"[A-Za-z0-9_.:-]{1,200}", business_key):
        raise ValueError("Invalid business-operation key")
    if type(units) is not int or not 1 <= units <= 1_000_000:
        raise ValueError("Units must be an integer between 1 and 1,000,000")
    effect_id = uuid4()
    result = {"effect_id": str(effect_id), "units": units}
    request_fingerprint = fingerprint({"units": units})
    with engine.begin() as connection:
        if protected:
            inserted = connection.execute(
                text("""
                    INSERT INTO relevo_demo.operations (business_key, request_fingerprint, result)
                    VALUES (:key, :fingerprint, :result)
                    ON CONFLICT (business_key) DO NOTHING RETURNING business_key
                """).bindparams(bindparam("result", type_=JSONB)),
                {"key": business_key, "fingerprint": request_fingerprint, "result": result},
            ).scalar_one_or_none()
            if inserted is None:
                original = (
                    connection.execute(
                        text(
                            "SELECT request_fingerprint, result FROM relevo_demo.operations "
                            "WHERE business_key=:key"
                        ),
                        {"key": business_key},
                    )
                    .mappings()
                    .one()
                )
                if original["request_fingerprint"] != request_fingerprint:
                    raise BusinessConflict("Business key was already used for different work")
                return original["result"]
        connection.execute(
            text("""
                INSERT INTO relevo_demo.effects
                    (id, business_key, operation_key, job_id, attempt_id, units, created_at)
                VALUES (:id, :key, :operation_key, :job_id, :attempt_id, :units, clock_timestamp())
            """),
            {
                "id": effect_id,
                "key": business_key,
                "operation_key": business_key if protected else None,
                "job_id": job_id,
                "attempt_id": attempt_id,
                "units": units,
            },
        )
    return result

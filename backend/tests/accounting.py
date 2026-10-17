"""Cross-table invariants checked after every real-PostgreSQL test."""

from sqlalchemy import Engine, text


def assert_job_accounting(engine: Engine) -> None:
    with engine.connect() as connection:
        for job in connection.execute(text("SELECT * FROM jobs")).mappings().all():
            attempts = (
                connection.execute(
                    text("SELECT * FROM attempts WHERE job_id=:id ORDER BY number"),
                    {"id": job["id"]},
                )
                .mappings()
                .all()
            )
            events = (
                connection.execute(
                    text("SELECT * FROM job_events WHERE job_id=:id ORDER BY sequence"),
                    {"id": job["id"]},
                )
                .mappings()
                .all()
            )
            assert len(attempts) == job["attempt_count"] <= job["max_attempts"]
            assert job["fencing_token"] == job["attempt_count"]
            assert [a["number"] for a in attempts] == list(range(1, len(attempts) + 1))
            assert [a["fencing_token"] for a in attempts] == list(range(1, len(attempts) + 1))
            assert [e["sequence"] for e in events] == list(range(1, job["event_sequence"] + 1))
            assert events[0]["kind"] == "submitted"
            assert events[-1]["data"]["state"] == job["state"]
            running = [a for a in attempts if a["state"] == "running"]
            assert len(running) == (1 if job["state"] == "running" else 0)
            if running:
                assert running[0]["id"] == job["current_attempt_id"]
            else:
                assert job["current_attempt_id"] is None
            assert len(events) == 1 + len(attempts) + sum(a["state"] != "running" for a in attempts)
            for attempt in attempts:
                matching = [e for e in events if e["attempt_id"] == attempt["id"]]
                assert matching[0]["kind"] == "claimed"
                assert matching[0]["data"]["fencing_token"] == attempt["fencing_token"]
                if attempt["state"] == "running":
                    assert len(matching) == 1
                else:
                    assert len(matching) == 2 and matching[1]["kind"] == attempt["state"]
                    assert attempt["finished_at"] is not None
            if job["state"] == "succeeded":
                assert attempts[-1]["state"] == "succeeded"
            if job["state"] == "failed":
                assert attempts[-1]["state"] in ("expired", "failed")

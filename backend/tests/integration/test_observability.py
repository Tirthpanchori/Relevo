import json
import logging
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter
from prometheus_client.parser import text_string_to_metric_families
from sqlalchemy import event

from relevo.api.app import create_app
from relevo.api.schemas import SubmitJob
from relevo.engine.jobs import submit_job

pytestmark = pytest.mark.integration


def samples(response):
    assert response.status_code == 200
    return {
        (s.name, tuple(sorted(s.labels.items()))): s.value
        for family in text_string_to_metric_families(response.text)
        for s in family.samples
    }


def test_durable_metrics_survive_api_recreation_but_request_counters_reset(
    api_client, db_engine, db_settings
):
    first = api_client.post(
        "/jobs",
        json={"task_type": "hash_payload", "payload": {}},
        headers={"Idempotency-Key": "metric-job"},
    )
    assert first.status_code == 201
    claim = api_client.post("/internal/claim", json={"worker_id": "metric-worker"}).json()
    assert (
        api_client.post(
            f"/internal/attempts/{claim['attempt_id']}/complete",
            json={
                "worker_id": "metric-worker",
                "fencing_token": claim["fencing_token"],
                "result": {"ok": True},
            },
        ).status_code
        == 200
    )
    before = samples(api_client.get("/metrics"))
    assert before[("relevo_jobs", (("state", "succeeded"),))] == 1
    assert before[("relevo_durable_queue_delay_seconds_count", ())] == 1
    assert before[("relevo_durable_attempt_duration_seconds_count", ())] == 1
    assert before[("relevo_database_metrics_up", ())] == 1
    with TestClient(create_app(db_settings)) as replacement:
        replacement.headers["Authorization"] = f"Bearer {db_settings.api_token.get_secret_value()}"
        after = samples(replacement.get("/metrics"))
    for key, value in before.items():
        if key[0].startswith("relevo_durable_") or key[0] == "relevo_jobs":
            assert after[key] == value
    assert not any(
        key[0] == "relevo_http_requests_total" and ("route", "/jobs") in key[1] for key in after
    )


def test_trace_parentage_and_metrics_exclude_payload_token_and_raw_paths(db_engine, db_settings):
    exporter = InMemorySpanExporter()
    app = create_app(db_settings)
    app.state.telemetry.provider.add_span_processor(SimpleSpanProcessor(exporter))
    private = "private-payload-never-log-this"
    with TestClient(app) as api:
        api.headers["Authorization"] = f"Bearer {db_settings.api_token.get_secret_value()}"
        response = api.post(
            "/jobs",
            json={"task_type": "hash_payload", "payload": {"secret": private}},
            headers={"Idempotency-Key": "trace-job"},
        )
        assert response.status_code == 201
        unknown = str(uuid4())
        assert api.get(f"/jobs/{unknown}").status_code == 404
        api.get(f"/unmatched/{private}")
        metric_text = api.get("/metrics").text
        assert unknown not in metric_text and private not in metric_text
        spans = exporter.get_finished_spans()
        engine_span = next(s for s in spans if s.name == "engine.submit")
        parent = next(s for s in spans if s.context.span_id == engine_span.parent.span_id)
        assert parent.name == "http.request"
        assert engine_span.attributes["relevo.job_id"] == response.json()["id"]
        exported = json.dumps(
            [
                {
                    "name": s.name,
                    "attributes": dict(s.attributes),
                    "events": [dict(e.attributes) for e in s.events],
                }
                for s in spans
            ]
        )
        assert private not in exported and db_settings.api_token.get_secret_value() not in exported
        assert db_settings.database_url.get_secret_value() not in exported


def test_rolled_back_submission_emits_no_committed_transition_log(db_engine, db_settings, caplog):
    def fail_event(conn, cursor, statement, parameters, context, executemany):
        if statement.lstrip().startswith("INSERT INTO job_events"):
            raise RuntimeError("controlled rollback")

    event.listen(db_engine, "before_cursor_execute", fail_event)
    try:
        with caplog.at_level(logging.INFO, logger="relevo.events"), pytest.raises(RuntimeError):
            submit_job(
                db_engine,
                db_settings,
                SubmitJob(task_type="hash_payload", payload={}),
                "rollback-log",
            )
    finally:
        event.remove(db_engine, "before_cursor_execute", fail_event)
    assert not any(r.getMessage() == "transition_committed" for r in caplog.records)

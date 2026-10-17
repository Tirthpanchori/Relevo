import json
import logging
import subprocess
import sys
from textwrap import dedent

import httpx
from fastapi.testclient import TestClient

from relevo.api.app import create_app
from relevo.observability import JsonFormatter, Telemetry


def test_unavailable_database_metrics_are_absent_instead_of_false_zero(unit_settings):
    with TestClient(create_app(unit_settings)) as api:
        api.headers["Authorization"] = f"Bearer {unit_settings.api_token.get_secret_value()}"
        response = api.get("/metrics")
        assert response.status_code == 200
        assert "relevo_database_metrics_up 0.0" in response.text
        assert "relevo_durable_transitions_total{" not in response.text
        assert unit_settings.database_url.get_secret_value() not in response.text


def test_json_logs_allowlisted_fields_and_omit_library_message_contents():
    formatter = JsonFormatter()
    record = logging.LogRecord(
        "relevo.events", logging.INFO, "", 1, "transition_committed", (), None
    )
    record.job_id = "job-safe"
    record.payload = "private-payload"
    record.api_token = "private-token"
    result = formatter.format(record)
    assert json.loads(result)["job_id"] == "job-safe" and "private" not in result
    library = logging.LogRecord("external-library", logging.ERROR, "", 1, "private-token", (), None)
    assert "private-token" not in formatter.format(library)


def test_worker_metrics_listener_requires_a_token():
    telemetry = Telemetry("worker-test")
    telemetry.serve(0, "private-token")
    try:
        with httpx.Client(trust_env=False, timeout=2) as client:
            url = f"http://127.0.0.1:{telemetry.server.server_port}/metrics"
            assert client.get(url).status_code == 401
            response = client.get(url, headers={"Authorization": "Bearer private-token"})
            assert (
                response.status_code == 200 and "relevo_worker_execution_seconds" in response.text
            )
            assert "private-token" not in response.text
    finally:
        telemetry.close()


def test_uvicorn_exception_logging_cannot_bypass_redaction():
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            dedent("""
            import logging.config
            from uvicorn.config import LOGGING_CONFIG
            from relevo.observability import configure_logging
            logging.config.dictConfig(LOGGING_CONFIG)
            configure_logging()
            try:
                raise RuntimeError("private-token-and-payload")
            except RuntimeError:
                logging.getLogger("uvicorn.error").exception("private-token-and-payload")
        """),
        ],
        capture_output=True,
        text=True,
        timeout=10,
        check=True,
    )
    assert "private-token-and-payload" not in result.stdout + result.stderr
    record = json.loads(result.stderr.strip())
    assert record["event"] == "library_message" and record["error_type"] == "RuntimeError"


def test_logging_setup_preserves_uvicorn_no_access_log():
    subprocess.run(
        [
            sys.executable,
            "-c",
            dedent("""
            import logging
            from uvicorn import Config
            from relevo.observability import configure_logging
            Config("unused:app", access_log=False)
            configure_logging()
            assert not logging.getLogger("uvicorn.access").hasHandlers()
        """),
        ],
        capture_output=True,
        text=True,
        timeout=10,
        check=True,
    )

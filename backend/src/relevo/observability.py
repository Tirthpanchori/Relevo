"""Process-local telemetry; durable accounting remains in PostgreSQL."""

import functools
import json
import logging
import secrets
from contextlib import contextmanager
from datetime import UTC, datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from threading import Thread
from time import perf_counter

from opentelemetry import propagate, trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, SimpleSpanProcessor
from opentelemetry.trace import Status, StatusCode
from prometheus_client import (
    CONTENT_TYPE_LATEST,
    CollectorRegistry,
    Counter,
    GCCollector,
    Histogram,
    PlatformCollector,
    ProcessCollector,
    generate_latest,
)
from sqlalchemy import event

logger = logging.getLogger("relevo.events")
BUCKETS = (0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2, 5, 10, 30, 60, 300, 3_600)
LOG_FIELDS = {
    "job_id",
    "attempt_id",
    "worker_id",
    "fencing_token",
    "state",
    "transition",
    "operation",
    "outcome",
    "sequence",
    "error_type",
    "seconds",
    "role",
}


class JsonFormatter(logging.Formatter):
    def format(self, record):
        data = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "event": record.getMessage() if record.name.startswith("relevo") else "library_message",
        }
        for key in LOG_FIELDS:
            if hasattr(record, key):
                value = getattr(record, key)
                data[key] = (
                    value if isinstance(value, (int, float, bool)) or value is None else str(value)
                )
        if record.exc_info and record.exc_info[0]:
            data["error_type"] = record.exc_info[0].__name__
        current = trace.get_current_span().get_span_context()
        if current.is_valid:
            data["trace_id"] = format(current.trace_id, "032x")
        return json.dumps(data, ensure_ascii=False)


def configure_logging() -> None:
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())
    logging.basicConfig(level=logging.INFO, handlers=[handler], force=True)
    # Uvicorn configures its own non-propagating handlers before loading the app.
    # Route those through the same redaction boundary, including uncaught exceptions.
    for name in ("uvicorn", "uvicorn.error", "uvicorn.access"):
        server_logger = logging.getLogger(name)
        server_logger.handlers.clear()
        server_logger.propagate = True
    logging.getLogger("httpx").setLevel(logging.WARNING)


def log_event(event_name: str, **fields) -> None:
    span = trace.get_current_span()
    for key in ("job_id", "attempt_id", "worker_id", "fencing_token", "transition"):
        if key in fields:
            span.set_attribute(f"relevo.{key}", str(fields[key]))
    logger.info(
        event_name, extra={key: value for key, value in fields.items() if key in LOG_FIELDS}
    )


class Telemetry:
    def __init__(self, role: str, *, endpoint: str | None = None, exporter=None):
        self.registry = CollectorRegistry()
        GCCollector(registry=self.registry)
        PlatformCollector(registry=self.registry)
        ProcessCollector(registry=self.registry)
        self.provider = TracerProvider(resource=Resource.create({"service.name": f"relevo-{role}"}))
        if exporter is not None:
            self.provider.add_span_processor(SimpleSpanProcessor(exporter))
        elif endpoint:
            self.provider.add_span_processor(
                BatchSpanProcessor(
                    OTLPSpanExporter(endpoint=endpoint, timeout=2),
                    max_queue_size=512,
                    max_export_batch_size=64,
                    schedule_delay_millis=500,
                )
            )
        self.tracer = self.provider.get_tracer("relevo")
        self.http_seconds = Histogram(
            "relevo_http_request_seconds",
            "API request wall time",
            ["method", "route", "status"],
            buckets=BUCKETS,
            registry=self.registry,
        )
        self.http_requests = Counter(
            "relevo_http_requests_total",
            "API responses",
            ["method", "route", "status"],
            registry=self.registry,
        )
        self.db_seconds = Histogram(
            "relevo_database_query_seconds",
            "SQL statement wall time",
            ["operation", "outcome"],
            buckets=BUCKETS,
            registry=self.registry,
        )
        self.rejections = Counter(
            "relevo_ownership_rejections_total",
            "Stale/conflicting ownership requests",
            ["operation"],
            registry=self.registry,
        )
        self.worker_seconds = Histogram(
            "relevo_worker_execution_seconds",
            "Child execution body elapsed time",
            ["outcome"],
            buckets=BUCKETS,
            registry=self.registry,
        )
        self.supervisor_seconds = Histogram(
            "relevo_worker_supervision_seconds",
            "Spawn through child cleanup",
            ["outcome"],
            buckets=BUCKETS,
            registry=self.registry,
        )
        self.worker_outcomes = Counter(
            "relevo_worker_outcomes_total",
            "Local worker outcomes",
            ["outcome"],
            registry=self.registry,
        )
        self.server = None
        self.server_thread = None

    @contextmanager
    def span(self, name, *, attributes=None, context=None):
        with self.tracer.start_as_current_span(
            name,
            attributes=attributes,
            context=context,
            record_exception=False,
            set_status_on_exception=False,
        ) as span:
            try:
                yield span
            except BaseException as exc:
                span.set_attribute("error.type", type(exc).__name__)
                span.set_status(Status(StatusCode.ERROR))
                raise

    def serve(self, port: int, token: str) -> None:
        registry = self.registry

        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):
                if not secrets.compare_digest(
                    self.headers.get("Authorization", "").encode(), f"Bearer {token}".encode()
                ):
                    self.send_error(401)
                    return
                if self.path != "/metrics":
                    self.send_error(404)
                    return
                body = generate_latest(registry)
                self.send_response(200)
                self.send_header("Content-Type", CONTENT_TYPE_LATEST)
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def log_message(self, *args):
                pass

        self.server = ThreadingHTTPServer(("0.0.0.0", port), Handler)
        self.server_thread = Thread(target=self.server.serve_forever, daemon=True)
        self.server_thread.start()

    def close(self):
        if self.server:
            self.server.shutdown()
            self.server.server_close()
            self.server_thread.join(timeout=2)
        self.provider.shutdown()


def instrument_engine(engine, telemetry: Telemetry) -> None:
    engine._relevo_telemetry = telemetry

    def before(conn, cursor, statement, parameters, context, executemany):
        word = statement.lstrip().split(maxsplit=1)[0].upper() if statement.strip() else "OTHER"
        operation = word if word in {"SELECT", "INSERT", "UPDATE", "DELETE"} else "OTHER"
        context._relevo_started = perf_counter()
        context._relevo_operation = operation
        context._relevo_span = telemetry.tracer.start_span(f"db.{operation}")

    def finish(context, outcome):
        if context is None or not hasattr(context, "_relevo_started"):
            return
        telemetry.db_seconds.labels(context._relevo_operation, outcome).observe(
            perf_counter() - context._relevo_started
        )
        if outcome == "error":
            context._relevo_span.set_status(Status(StatusCode.ERROR))
        context._relevo_span.end()
        del context._relevo_started

    event.listen(engine, "before_cursor_execute", before)
    event.listen(
        engine, "after_cursor_execute", lambda conn, cur, stmt, params, ctx, many: finish(ctx, "ok")
    )
    event.listen(engine, "handle_error", lambda context: finish(context.execution_context, "error"))


def observed(operation):
    def decorate(function):
        @functools.wraps(function)
        def wrapped(*args, **kwargs):
            engine = args[0] if args else kwargs["engine"]
            telemetry = getattr(engine, "_relevo_telemetry", None)
            if telemetry is None:
                return function(*args, **kwargs)
            with telemetry.span(f"engine.{operation}"):
                return function(*args, **kwargs)

        return wrapped

    return decorate


class HttpTelemetry:
    def __init__(self, app, telemetry):
        self.app, self.telemetry = app, telemetry

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)
        started, status = perf_counter(), 500
        headers = {key.decode("latin1"): value.decode("latin1") for key, value in scope["headers"]}

        async def record_send(message):
            nonlocal status
            if message["type"] == "http.response.start":
                status = message["status"]
            await send(message)

        with self.telemetry.span("http.request", context=propagate.extract(headers)) as span:
            try:
                await self.app(scope, receive, record_send)
            finally:
                route = getattr(scope.get("route"), "path", "unmatched")
                method = scope["method"] if scope["method"] in {"GET", "POST"} else "OTHER"
                labels = method, route, str(status)
                self.telemetry.http_requests.labels(*labels).inc()
                self.telemetry.http_seconds.labels(*labels).observe(perf_counter() - started)
                span.set_attributes(
                    {
                        "http.request.method": method,
                        "http.route": route,
                        "http.response.status_code": status,
                    }
                )
                if status >= 500:
                    span.set_status(Status(StatusCode.ERROR))

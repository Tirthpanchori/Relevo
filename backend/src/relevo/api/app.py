"""Application factory with explicit configuration, authentication, and error boundaries."""

import logging
import secrets
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Annotated
from uuid import UUID

from fastapi import Depends, FastAPI, Header, HTTPException, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from sqlalchemy.exc import SQLAlchemyError
from starlette.exceptions import HTTPException as StarletteHTTPException

from relevo import __version__
from relevo.api.middleware import RequestSizeLimit
from relevo.api.schemas import (
    AttemptHistory,
    ClaimRequest,
    ClaimResponse,
    CompleteRequest,
    ErrorEnvelope,
    FailRequest,
    Health,
    HeartbeatResponse,
    JobView,
    OutcomeResponse,
    Ownership,
    SubmitJob,
)
from relevo.config import Settings
from relevo.db.connection import build_engine, database_ready, schema_head
from relevo.engine.errors import EngineError
from relevo.engine.jobs import get_attempts, get_job, submit_job
from relevo.engine.ownership import claim_job, renew_lease, report_outcome
from relevo.observability import HttpTelemetry, Telemetry, configure_logging, instrument_engine
from relevo.observability_db import DurableCollector

logger = logging.getLogger(__name__)
bearer = HTTPBearer(auto_error=False)


def error_response(status: int, code: str, message: str, **kwargs: object) -> JSONResponse:
    return JSONResponse(
        status_code=status,
        content={"error": {"code": code, "message": message, "details": []}},
        **kwargs,
    )


def create_app(settings: Settings | None = None) -> FastAPI:
    if settings is None:
        configure_logging()
        settings = Settings()
    engine = build_engine(settings)
    telemetry = Telemetry(
        "api", endpoint=str(settings.otlp_endpoint) if settings.otlp_endpoint else None
    )
    instrument_engine(engine, telemetry)
    telemetry.registry.register(DurableCollector(engine))
    expected_head = schema_head()

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        try:
            yield
        finally:
            telemetry.close()
            engine.dispose()

    app = FastAPI(
        title="Relevo",
        version=__version__,
        lifespan=lifespan,
        description="Durable submission and leased coordination for supervised Python workers.",
    )
    app.state.engine = engine
    app.state.settings = settings
    app.state.telemetry = telemetry
    app.add_middleware(HttpTelemetry, telemetry=telemetry)
    app.add_middleware(RequestSizeLimit, max_bytes=settings.max_request_bytes)

    def authenticate(
        credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
    ) -> None:
        if credentials is None or not secrets.compare_digest(
            credentials.credentials.encode(),
            settings.api_token.get_secret_value().encode(),
        ):
            raise HTTPException(
                status_code=401,
                detail="A valid bearer token is required",
                headers={"WWW-Authenticate": "Bearer"},
            )

    @app.exception_handler(EngineError)
    async def engine_error(request: Request, exc: EngineError) -> JSONResponse:
        if exc.code == "ownership_conflict":
            operation = request.url.path.rsplit("/", 1)[-1]
            if operation in {"heartbeat", "complete", "fail"}:
                telemetry.rejections.labels(operation).inc()
        return error_response(exc.status_code, exc.code, str(exc))

    @app.exception_handler(SQLAlchemyError)
    async def database_error(request: Request, exc: SQLAlchemyError) -> JSONResponse:
        # SQL/parameters/DSNs can contain secrets or payloads; log only the error class.
        logger.warning("Database operation failed: %s", type(exc).__name__)
        return error_response(
            503,
            "database_unavailable",
            "Database operation could not be confirmed; retry safely",
            headers={"Retry-After": "1"},
        )

    @app.exception_handler(RequestValidationError)
    async def validation_error(request: Request, exc: RequestValidationError) -> JSONResponse:
        return JSONResponse(
            status_code=422,
            content={
                "error": {
                    "code": "validation_error",
                    "message": "Request validation failed",
                    "details": [
                        {"location": list(error["loc"]), "type": error["type"]}
                        for error in exc.errors()
                    ],
                }
            },
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_error(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        return error_response(
            exc.status_code,
            {401: "unauthorized", 404: "not_found", 501: "not_implemented"}.get(
                exc.status_code,
                "http_error",
            ),
            str(exc.detail),
            headers=exc.headers,
        )

    errors = {code: {"model": ErrorEnvelope} for code in (401, 404, 409, 413, 422, 503)}
    protected = [Depends(authenticate)]

    @app.get("/health/live", response_model=Health, tags=["health"])
    def live() -> Health:
        return Health(status="ok")

    @app.get(
        "/health/ready", response_model=Health, responses={503: {"model": Health}}, tags=["health"]
    )
    def ready(response: Response) -> Health:
        try:
            is_ready = database_ready(engine, expected_head)
        except SQLAlchemyError:
            is_ready = False
        if not is_ready:
            response.status_code = 503
        return Health(status="ready" if is_ready else "not_ready")

    @app.post(
        "/jobs",
        response_model=JobView,
        status_code=201,
        dependencies=protected,
        responses={**errors, 200: {"model": JobView, "description": "Existing submission"}},
        tags=["jobs"],
    )
    def submit(
        body: SubmitJob,
        response: Response,
        idempotency_key: Annotated[
            str,
            Header(min_length=1, max_length=200, pattern=r"^[A-Za-z0-9_.:-]+$"),
        ],
    ) -> JobView:
        job, created = submit_job(engine, settings, body, idempotency_key)
        response.status_code = 201 if created else 200
        response.headers["Location"] = f"/jobs/{job.id}"
        return job

    @app.get(
        "/jobs/{id}",
        response_model=JobView,
        dependencies=protected,
        responses=errors,
        tags=["jobs"],
    )
    def inspect_job(id: UUID) -> JobView:
        return get_job(engine, id)

    @app.get(
        "/jobs/{id}/attempts",
        response_model=AttemptHistory,
        dependencies=protected,
        responses=errors,
        tags=["jobs"],
    )
    def attempts(id: UUID) -> AttemptHistory:
        return get_attempts(engine, id)

    @app.post(
        "/internal/claim",
        response_model=ClaimResponse,
        dependencies=protected,
        responses={**errors, 204: {"description": "No eligible work"}},
        tags=["internal"],
    )
    def claim(body: ClaimRequest) -> ClaimResponse | Response:
        assignment = claim_job(engine, settings, body.worker_id)
        return assignment if assignment is not None else Response(status_code=204)

    @app.post(
        "/internal/attempts/{id}/heartbeat",
        response_model=HeartbeatResponse,
        dependencies=protected,
        responses=errors,
        tags=["internal"],
    )
    def heartbeat(id: UUID, body: Ownership) -> HeartbeatResponse:
        return renew_lease(engine, settings, id, body)

    @app.post(
        "/internal/attempts/{id}/complete",
        response_model=OutcomeResponse,
        dependencies=protected,
        responses=errors,
        tags=["internal"],
    )
    def complete(id: UUID, body: CompleteRequest) -> OutcomeResponse:
        return report_outcome(engine, settings, id, body)

    @app.post(
        "/internal/attempts/{id}/fail",
        response_model=OutcomeResponse,
        dependencies=protected,
        responses=errors,
        tags=["internal"],
    )
    def fail(id: UUID, body: FailRequest) -> OutcomeResponse:
        return report_outcome(engine, settings, id, body)

    @app.get("/metrics", dependencies=protected, response_class=Response, tags=["operations"])
    def metrics() -> Response:
        return Response(generate_latest(telemetry.registry), media_type=CONTENT_TYPE_LATEST)

    return app

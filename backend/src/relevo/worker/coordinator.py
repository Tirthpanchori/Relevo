"""HTTPX with a total async deadline, bounded responses, and no automatic claim retries."""

import asyncio
import json
from typing import Any
from uuid import UUID

import httpx
from opentelemetry import propagate
from pydantic import ValidationError

from relevo.api.schemas import ClaimResponse, HeartbeatResponse, OutcomeResponse
from relevo.worker.config import WorkerSettings


class CoordinatorUnavailable(Exception):
    """The request's outcome is uncertain; no error body or credentials are exposed."""


class OwnershipLost(Exception):
    pass


class CoordinatorRejected(Exception):
    pass


class CoordinatorClient:
    def __init__(self, settings: WorkerSettings, *, transport=None, telemetry=None) -> None:
        self.settings = settings
        self.telemetry = telemetry
        self.http = httpx.AsyncClient(
            base_url=str(settings.api_url),
            headers={"Authorization": f"Bearer {settings.api_token.get_secret_value()}"},
            timeout=settings.http_timeout_seconds,
            follow_redirects=False,
            trust_env=False,
            transport=transport,
        )

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        await self.http.aclose()

    async def post(self, path: str, body: dict, *, budget: float | None = None) -> tuple[int, Any]:
        timeout = (
            self.settings.http_timeout_seconds
            if budget is None
            else min(
                budget,
                self.settings.http_timeout_seconds,
            )
        )
        if timeout <= 0:
            raise CoordinatorUnavailable("Request deadline has elapsed")
        headers = {}
        propagate.inject(headers)
        try:
            async with (
                asyncio.timeout(timeout),
                self.http.stream("POST", path, json=body, headers=headers) as response,
            ):
                raw = bytearray()
                async for chunk in response.aiter_bytes():
                    raw.extend(chunk)
                    if len(raw) > 1_048_576:
                        raise CoordinatorRejected("Coordinator response exceeds the byte limit")
                if response.status_code == 204:
                    return 204, None
                if response.status_code >= 500:
                    raise CoordinatorUnavailable("Coordinator operation could not be confirmed")
                if response.status_code in (404, 409) and path != "/internal/claim":
                    raise OwnershipLost("The coordinator rejected this attempt's ownership")
                if response.status_code != 200:
                    raise CoordinatorRejected(
                        f"Coordinator rejected request with HTTP {response.status_code}"
                    )
                try:
                    return response.status_code, json.loads(raw)
                except (ValueError, UnicodeDecodeError) as exc:
                    raise CoordinatorRejected("Coordinator returned invalid JSON") from exc
        except (httpx.TransportError, TimeoutError) as exc:
            raise CoordinatorUnavailable("Coordinator request could not be confirmed") from exc

    async def claim(self, worker_id: str) -> ClaimResponse | None:
        status, data = await self.post("/internal/claim", {"worker_id": worker_id})
        if status == 204:
            return None
        try:
            return ClaimResponse.model_validate(data)
        except ValidationError as exc:
            raise CoordinatorRejected("Coordinator returned an invalid claim") from exc

    async def heartbeat(self, attempt_id: UUID, body: dict, *, budget: float) -> HeartbeatResponse:
        _, data = await self.post(f"/internal/attempts/{attempt_id}/heartbeat", body, budget=budget)
        try:
            response = HeartbeatResponse.model_validate(data)
            if response.attempt_id != attempt_id:
                raise CoordinatorRejected("Heartbeat response identifies another attempt")
            return response
        except ValidationError as exc:
            raise CoordinatorRejected("Coordinator returned an invalid heartbeat") from exc

    async def report(self, attempt_id: UUID, kind: str, body: dict) -> OutcomeResponse:
        _, data = await self.post(f"/internal/attempts/{attempt_id}/{kind}", body)
        try:
            response = OutcomeResponse.model_validate(data)
            if response.attempt_id != attempt_id:
                raise CoordinatorRejected("Outcome response identifies another attempt")
            return response
        except ValidationError as exc:
            raise CoordinatorRejected("Coordinator returned an invalid outcome") from exc

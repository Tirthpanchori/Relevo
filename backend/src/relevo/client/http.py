"""Bounded HTTP requests and explicit, immutable submission retries."""

import asyncio
import json
import math
import re
from uuid import UUID

import httpx
from pydantic import ValidationError

from relevo.api.schemas import AttemptHistory, JobView, SubmitJob
from relevo.client.config import ClientSettings
from relevo.engine.serialization import canonical_json


class ClientError(Exception):
    def __init__(self, message: str, *, status_code: int | None = None):
        super().__init__(message)
        self.status_code = status_code


class ClientUnavailable(ClientError):
    """No acceptance/rejection can be inferred from this error."""


class RelevoClient:
    def __init__(self, settings: ClientSettings, *, transport=None):
        self.settings = settings
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

    async def request(self, method: str, path: str, *, content=None, headers=None):
        try:
            async with (
                asyncio.timeout(self.settings.http_timeout_seconds),
                self.http.stream(method, path, content=content, headers=headers) as response,
            ):
                if response.status_code >= 500:
                    raise ClientUnavailable("Coordinator operation could not be confirmed")
                if response.status_code not in (200, 201):
                    raise ClientError(
                        f"Coordinator rejected request with HTTP {response.status_code}",
                        status_code=response.status_code,
                    )
                raw = bytearray()
                async for chunk in response.aiter_bytes():
                    raw.extend(chunk)
                    if len(raw) > 1_048_576:
                        raise ClientError("Coordinator response exceeds the byte limit")
                try:
                    return json.loads(raw)
                except (ValueError, UnicodeDecodeError, RecursionError) as exc:
                    raise ClientError("Coordinator returned invalid JSON") from exc
        except (httpx.TransportError, TimeoutError) as exc:
            raise ClientUnavailable("Coordinator request could not be confirmed") from exc

    @staticmethod
    def parse(model, value):
        try:
            return model.model_validate(value)
        except ValidationError as exc:
            raise ClientError("Coordinator returned an invalid response") from exc

    async def submit(self, request: SubmitJob, *, idempotency_key: str) -> JobView:
        if not re.fullmatch(r"[A-Za-z0-9_.:-]{1,200}", idempotency_key):
            raise ValueError("Idempotency key must use 1-200 letters, digits, dots, colons, _ or -")
        # Freeze before the first await: mutations or response loss cannot change a retry's work.
        encoded = canonical_json(request.model_dump(mode="json"))
        headers = {"Content-Type": "application/json", "Idempotency-Key": idempotency_key}
        for number in range(self.settings.submission_attempts):
            try:
                data = await self.request("POST", "/jobs", content=encoded, headers=headers)
                return self.parse(JobView, data)
            except ClientUnavailable:
                if number + 1 == self.settings.submission_attempts:
                    raise ClientUnavailable(
                        "Submission remains uncertain; retry with the same idempotency key "
                        "and request"
                    ) from None
                await asyncio.sleep(min(2, 0.2 * 2**number))
        raise AssertionError("submission_attempts must be positive")

    async def inspect(self, job_id: UUID) -> JobView:
        job_id = UUID(str(job_id))
        job = self.parse(JobView, await self.request("GET", f"/jobs/{job_id}"))
        if job.id != job_id:
            raise ClientError("Coordinator response identifies another job")
        return job

    async def attempts(self, job_id: UUID) -> AttemptHistory:
        job_id = UUID(str(job_id))
        history = self.parse(AttemptHistory, await self.request("GET", f"/jobs/{job_id}/attempts"))
        if history.job_id != job_id or any(a.job_id != job_id for a in history.attempts):
            raise ClientError("Coordinator response identifies another job")
        return history

    async def wait(
        self, job_id: UUID, *, timeout: float = 60, poll_seconds: float = 0.25
    ) -> JobView:
        if not (math.isfinite(timeout) and 0 < timeout <= 3_600):
            raise ValueError("Wait timeout must be positive and at most 3,600 seconds")
        if not (math.isfinite(poll_seconds) and 0 < poll_seconds <= 30):
            raise ValueError("Poll interval must be positive and at most 30 seconds")
        try:
            async with asyncio.timeout(timeout):
                while True:
                    try:
                        job = await self.inspect(job_id)
                    except ClientUnavailable:
                        pass
                    else:
                        if job.state in ("succeeded", "failed"):
                            return job
                    await asyncio.sleep(poll_seconds)
        except TimeoutError:
            raise ClientUnavailable(
                "Wait deadline elapsed; inspect the saved job ID later"
            ) from None

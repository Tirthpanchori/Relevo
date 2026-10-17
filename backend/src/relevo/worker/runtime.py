"""One assignment at a time, supervised using monotonic time and confirmed leases."""

import asyncio
import logging
import math
import multiprocessing
import tempfile
import uuid
from contextlib import suppress
from pathlib import Path
from time import monotonic

from opentelemetry import trace
from pydantic import ValidationError

from relevo.api.schemas import ClaimResponse, CompleteRequest, FailRequest
from relevo.observability import log_event
from relevo.worker.child import execute_child, read_result
from relevo.worker.config import WorkerSettings
from relevo.worker.coordinator import (
    CoordinatorClient,
    CoordinatorRejected,
    CoordinatorUnavailable,
    OwnershipLost,
)

logger = logging.getLogger(__name__)


def stop_child(process: multiprocessing.Process) -> None:
    if process.is_alive():
        process.terminate()
    process.join(timeout=1)
    if process.is_alive():
        process.kill()
        process.join(timeout=1)
    if process.is_alive():
        raise RuntimeError("Could not stop and reap the handler process")


class Worker:
    def __init__(
        self,
        client: CoordinatorClient,
        settings: WorkerSettings,
        *,
        worker_id: str | None = None,
        stop: asyncio.Event | None = None,
        work_directory: Path | None = None,
    ) -> None:
        self.client = client
        self.settings = settings
        self.worker_id = worker_id or f"worker-{uuid.uuid4()}"
        self.stop = stop or asyncio.Event()
        self.work_directory = work_directory
        self.context = multiprocessing.get_context("spawn")
        self.active_process = None

    async def pause(self, seconds: float) -> None:
        with suppress(TimeoutError):
            await asyncio.wait_for(self.stop.wait(), timeout=max(0.001, seconds))

    async def run_once(self) -> str:
        telemetry = self.client.telemetry
        if telemetry is None:
            return await self._run_once()
        with telemetry.span("worker.assignment") as span:
            outcome = await self._run_once()
            telemetry.worker_outcomes.labels(outcome).inc()
            span.set_attribute("relevo.outcome", outcome)
            return outcome

    async def _run_once(self) -> str:
        claim_started = monotonic()
        try:
            assignment = await self.client.claim(self.worker_id)
        except CoordinatorUnavailable:
            # Claim may have committed. Do not execute or invent an assignment on uncertainty.
            return "unavailable"
        if assignment is None:
            return "idle"
        trace.get_current_span().set_attributes(
            {
                "relevo.job_id": str(assignment.job_id),
                "relevo.attempt_id": str(assignment.attempt_id),
                "relevo.worker_id": self.worker_id,
                "relevo.fencing_token": assignment.fencing_token,
            }
        )
        log_event(
            "worker_claim_received",
            job_id=assignment.job_id,
            attempt_id=assignment.attempt_id,
            worker_id=self.worker_id,
            fencing_token=assignment.fencing_token,
            state="running",
        )
        if self.stop.is_set():
            return "ownership_lost"
        lease_deadline = claim_started + assignment.lease_seconds
        if monotonic() >= lease_deadline:
            return "ownership_lost"
        with tempfile.TemporaryDirectory(
            prefix="relevo-attempt-", dir=self.work_directory
        ) as directory:
            path = Path(directory) / "outcome.json"
            process = self.context.Process(
                target=execute_child,
                args=(
                    assignment.task_type,
                    assignment.payload,
                    assignment.attempt_number,
                    assignment.max_result_bytes,
                    str(path),
                    claim_started + assignment.task_timeout_seconds,
                ),
            )
            supervision_started = monotonic()
            try:
                process.start()
            except (OSError, RuntimeError):
                process.close()
                return await self.deliver(
                    assignment,
                    {
                        "kind": "fail",
                        "error": {
                            "code": "handler_start_failed",
                            "message": "Handler process could not start",
                        },
                        "retryable": True,
                    },
                )
            self.active_process = process
            envelope = None
            try:
                envelope = await self.supervise(
                    process, assignment, path, lease_deadline, claim_started
                )
            finally:
                stop_child(process)
                process.close()
                self.active_process = None
                if self.client.telemetry:
                    self.client.telemetry.supervisor_seconds.labels(
                        envelope["kind"] if envelope else "ownership_lost"
                    ).observe(monotonic() - supervision_started)
            if envelope is None:
                return "ownership_lost"
            return await self.deliver(assignment, envelope)

    async def supervise(
        self,
        process,
        assignment: ClaimResponse,
        path: Path,
        lease_deadline: float,
        started: float,
    ) -> dict | None:
        task_deadline = started + assignment.task_timeout_seconds
        interval = min(self.settings.heartbeat_seconds, assignment.lease_seconds / 3)
        next_heartbeat = started + interval
        ownership = {"worker_id": self.worker_id, "fencing_token": assignment.fencing_token}
        while True:
            now = monotonic()
            if self.stop.is_set() or now >= lease_deadline:
                return None
            if not process.is_alive():
                process.join(timeout=0)
                if process.exitcode != 0 or not path.exists():
                    return {
                        "kind": "fail",
                        "error": {
                            "code": "handler_crashed",
                            "message": "Handler exited without a valid outcome",
                        },
                        "retryable": True,
                    }
                try:
                    envelope = read_result(path, assignment.max_result_bytes)
                    if not isinstance(envelope, dict):
                        raise ValueError("Invalid envelope")
                    kind = envelope.pop("kind", None)
                    handler_seconds = envelope.pop("_handler_seconds", None)
                    model = CompleteRequest if kind == "complete" else FailRequest
                    if kind not in ("complete", "fail"):
                        raise ValueError("Unknown envelope")
                    validated = model.model_validate({**ownership, **envelope})
                    # Optional telemetry must never change a valid business outcome.
                    if (
                        self.client.telemetry
                        and not isinstance(handler_seconds, bool)
                        and isinstance(handler_seconds, (int, float))
                        and math.isfinite(handler_seconds)
                        and handler_seconds >= 0
                    ):
                        self.client.telemetry.worker_seconds.labels(kind).observe(handler_seconds)
                    return {"kind": kind, **validated.model_dump(mode="json")}
                except (OSError, ValueError, ValidationError, TypeError):
                    return {
                        "kind": "fail",
                        "error": {
                            "code": "invalid_result",
                            "message": "Handler produced an invalid outcome",
                        },
                        "retryable": False,
                    }
            if now >= task_deadline:
                return {
                    "kind": "fail",
                    "error": {
                        "code": "execution_timeout",
                        "message": "Task exceeded its execution deadline",
                    },
                    "retryable": True,
                }
            if now >= next_heartbeat:
                renewal_started = monotonic()
                try:
                    renewed = await self.client.heartbeat(
                        assignment.attempt_id,
                        ownership,
                        budget=min(lease_deadline, task_deadline) - renewal_started,
                    )
                except (CoordinatorUnavailable, CoordinatorRejected, OwnershipLost):
                    return None
                lease_deadline = renewal_started + renewed.lease_seconds
                interval = min(self.settings.heartbeat_seconds, renewed.lease_seconds / 3)
                next_heartbeat = renewal_started + interval
                continue
            await self.pause(
                min(
                    self.settings.worker_monitor_seconds,
                    lease_deadline - now,
                    task_deadline - now,
                    next_heartbeat - now,
                )
            )

    async def deliver(self, assignment: ClaimResponse, envelope: dict) -> str:
        kind = envelope["kind"]
        body = {key: value for key, value in envelope.items() if key != "kind"}
        body.update(worker_id=self.worker_id, fencing_token=assignment.fencing_token)
        for number in range(self.settings.worker_report_attempts):
            if self.stop.is_set():
                return "ownership_lost"
            try:
                outcome = await self.client.report(assignment.attempt_id, kind, body)
                if outcome.job_id != assignment.job_id:
                    raise CoordinatorRejected("Outcome response identifies another job")
                log_event(
                    "worker_outcome_acknowledged",
                    job_id=assignment.job_id,
                    attempt_id=assignment.attempt_id,
                    worker_id=self.worker_id,
                    fencing_token=assignment.fencing_token,
                    state=outcome.state,
                )
                return "reported"
            except OwnershipLost:
                return "ownership_lost"
            except CoordinatorUnavailable:
                if number + 1 < self.settings.worker_report_attempts:
                    await self.pause(min(2, 0.2 * 2**number))
        # Never rerun the handler here. The coordinator may already have committed the report.
        return "unavailable"

    async def run_forever(self) -> None:
        failures = 0
        while not self.stop.is_set():
            outcome = await self.run_once()
            failures = failures + 1 if outcome in ("unavailable", "ownership_lost") else 0
            delay = (
                min(self.settings.worker_backoff_seconds, 0.25 * 2 ** min(failures, 8))
                if failures
                else self.settings.worker_poll_seconds
            )
            if outcome != "reported":
                logger.info("Worker poll ended: worker=%s outcome=%s", self.worker_id, outcome)
                await self.pause(delay)

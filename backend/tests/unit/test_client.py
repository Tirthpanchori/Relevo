import asyncio
import json
import sys
from datetime import UTC, datetime
from uuid import uuid4

import httpx
import pytest
from pydantic import ValidationError

from relevo.api.schemas import SubmitJob
from relevo.client import ClientError, ClientSettings, ClientUnavailable, RelevoClient
from relevo.client.cli import main

TOKEN = "client-test-token-never-use-in-production-1234"


def settings(**changes):
    return ClientSettings(api_url="http://coordinator.test", api_token=TOKEN, **changes)


def job_response(**changes):
    now = datetime.now(UTC).isoformat()
    return {
        "id": str(uuid4()),
        "task_type": "hash_payload",
        "payload": {},
        "run_at": None,
        "state": "pending",
        "available_at": now,
        "created_at": now,
        "updated_at": now,
        "finished_at": None,
        "max_attempts": 3,
        "attempt_count": 0,
        **changes,
    }


def test_submission_retries_identical_bytes_and_key_even_if_callers_mutate_input():
    bodies = []
    request = SubmitJob(task_type="hash_payload", payload={"original": True})
    response = job_response(payload={"original": True})

    def transport(req):
        bodies.append((req.content, req.headers["Idempotency-Key"]))
        assert req.headers["Authorization"] == f"Bearer {TOKEN}"
        if len(bodies) == 1:
            request.payload["original"] = False
            raise httpx.ReadTimeout("private diagnostic that must not escape")
        return httpx.Response(200, json=response)

    async def run():
        async with RelevoClient(settings(), transport=httpx.MockTransport(transport)) as client:
            job = await client.submit(request, idempotency_key="original-key")
            assert str(job.id) == response["id"]

    asyncio.run(run())
    assert len(bodies) == 2 and bodies[0] == bodies[1]
    assert json.loads(bodies[0][0])["payload"] == {"original": True}


@pytest.mark.parametrize("status", [401, 404, 409, 413, 422, 302])
def test_definitive_rejections_are_not_retried_or_echoed(status):
    calls = []

    def transport(request):
        calls.append(request)
        return httpx.Response(status, text=f"private {TOKEN}")

    async def run():
        async with RelevoClient(settings(), transport=httpx.MockTransport(transport)) as client:
            with pytest.raises(ClientError) as caught:
                await client.submit(
                    SubmitJob(task_type="hash_payload", payload={}), idempotency_key="k"
                )
            assert caught.value.status_code == status
            assert TOKEN not in str(caught.value) and "private" not in str(caught.value)

    asyncio.run(run())
    assert len(calls) == 1


def test_uncertain_submission_has_a_bounded_retry_budget():
    calls = []

    def transport(request):
        calls.append(request)
        return httpx.Response(503)

    async def run():
        async with RelevoClient(
            settings(submission_attempts=2), transport=httpx.MockTransport(transport)
        ) as client:
            with pytest.raises(ClientUnavailable, match="same idempotency key"):
                await client.submit(
                    SubmitJob(task_type="hash_payload", payload={}), idempotency_key="k"
                )

    asyncio.run(run())
    assert len(calls) == 2


@pytest.mark.parametrize(
    "body",
    [b"invalid JSON", b"{}", b"x" * 1_048_577],
    ids=["invalid-json", "invalid-contract", "oversized"],
)
def test_invalid_success_responses_are_bounded_and_redacted(body):
    async def run():
        async with RelevoClient(
            settings(), transport=httpx.MockTransport(lambda req: httpx.Response(200, content=body))
        ) as client:
            with pytest.raises(ClientError):
                await client.inspect(uuid4())

    asyncio.run(run())


def test_wait_has_a_total_deadline_even_when_coordinator_stalls():
    async def stalled(request):
        await asyncio.Event().wait()

    async def run():
        async with RelevoClient(settings(), transport=httpx.MockTransport(stalled)) as client:
            with pytest.raises(ClientUnavailable, match="Wait deadline"):
                await asyncio.wait_for(client.wait(uuid4(), timeout=0.05), timeout=1)

    asyncio.run(run())


def test_inspection_and_history_reject_mismatching_job_ids():
    async def run():
        for path in ("inspect", "attempts"):
            value = (
                job_response() if path == "inspect" else {"job_id": str(uuid4()), "attempts": []}
            )
            async with RelevoClient(
                settings(),
                transport=httpx.MockTransport(
                    lambda req, body=value: httpx.Response(200, json=body)
                ),
            ) as client:
                with pytest.raises(ClientError, match="another job"):
                    await getattr(client, path)(uuid4())

    asyncio.run(run())


@pytest.mark.parametrize("key", ["", "has spaces", "x" * 201, "bad\nheader"])
def test_submission_keys_are_validated_before_transport(key):
    def transport(request):
        pytest.fail("Invalid keys must never reach the transport")

    async def run():
        async with RelevoClient(settings(), transport=httpx.MockTransport(transport)) as client:
            with pytest.raises(ValueError):
                await client.submit(
                    SubmitJob(task_type="hash_payload", payload={}), idempotency_key=key
                )

    asyncio.run(run())


def test_explicit_client_configuration_is_required(monkeypatch):
    monkeypatch.delenv("RELEVO_API_URL", raising=False)
    monkeypatch.delenv("RELEVO_API_TOKEN", raising=False)
    with pytest.raises(ValidationError):
        ClientSettings()


@pytest.mark.parametrize("url", ["http://user:pass@host", "http://host/jobs", "http://host?key=x"])
def test_client_configuration_requires_a_clean_origin(url):
    with pytest.raises(ValidationError):
        ClientSettings(api_url=url, api_token=TOKEN)


def test_cli_configuration_errors_do_not_echo_secrets(monkeypatch, capsys):
    monkeypatch.setenv("RELEVO_API_TOKEN", TOKEN)
    monkeypatch.setenv("RELEVO_API_URL", "http://user:private-password@host")
    monkeypatch.setattr(sys, "argv", ["relevo", "inspect", str(uuid4())])
    with pytest.raises(SystemExit) as caught:
        main()
    assert caught.value.code == 2
    output = capsys.readouterr()
    assert TOKEN not in output.err and "private-password" not in output.err


def test_cli_bad_json_is_rejected_without_echoing_payload(monkeypatch, capsys):
    monkeypatch.setenv("RELEVO_API_TOKEN", TOKEN)
    monkeypatch.setenv("RELEVO_API_URL", "http://coordinator.test")
    monkeypatch.setattr(
        sys,
        "argv",
        ["relevo", "submit", "hash_payload", "--key", "key", "--payload", "private invalid JSON"],
    )
    with pytest.raises(SystemExit) as caught:
        main()
    assert caught.value.code == 1
    assert "private" not in capsys.readouterr().err

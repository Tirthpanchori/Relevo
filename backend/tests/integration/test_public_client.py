import asyncio

import httpx
import pytest
from sqlalchemy import Engine, text

from relevo.api.app import create_app
from relevo.api.schemas import SubmitJob
from relevo.client import ClientError, ClientSettings, RelevoClient
from relevo.config import Settings
from relevo.worker.config import WorkerSettings
from relevo.worker.coordinator import CoordinatorClient
from relevo.worker.runtime import Worker

pytestmark = pytest.mark.integration


def test_public_client_recovers_a_lost_submission_and_observes_real_execution(
    db_engine: Engine, db_settings: Settings, tmp_path
):
    async def run():
        app = create_app(db_settings)
        adapter = httpx.ASGITransport(app=app)
        calls = []

        async def lose_first_response(request):
            response = await adapter.handle_async_request(request)
            await response.aread()
            if request.method == "POST":
                calls.append(response.status_code)
                if len(calls) == 1:
                    raise httpx.ReadTimeout("Controlled loss after committed acceptance")
            return response

        async with (
            app.router.lifespan_context(app),
            RelevoClient(
                ClientSettings(api_url="http://test", api_token=db_settings.api_token),
                transport=httpx.MockTransport(lose_first_response),
            ) as public,
        ):
            request = SubmitJob(task_type="hash_payload", payload={"client": "actual"})
            job = await public.submit(request, idempotency_key="public-lost-response")
            assert calls == [201, 200]
            assert (await public.inspect(job.id)).state == "pending"
            assert not (await public.attempts(job.id)).attempts
            with pytest.raises(ClientError) as conflict:
                await public.submit(
                    SubmitJob(task_type="hash_payload", payload={"changed": True}),
                    idempotency_key="public-lost-response",
                )
            assert conflict.value.status_code == 409
            worker_settings = WorkerSettings(api_token=db_settings.api_token)
            async with CoordinatorClient(worker_settings, transport=adapter) as coordinator:
                worker = Worker(coordinator, worker_settings, work_directory=tmp_path)
                assert await worker.run_once() == "reported"
            assert (await public.wait(job.id, timeout=2)).state == "succeeded"
            assert len((await public.attempts(job.id)).attempts) == 1

    asyncio.run(run())
    with db_engine.connect() as connection:
        assert connection.execute(text("SELECT count(*) FROM jobs")).scalar_one() == 1

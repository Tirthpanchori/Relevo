"""Verify local scrape targets, provisioned dashboard, and actual distributed trace export."""

import argparse
import asyncio
import json
import os
from datetime import UTC, datetime, timedelta
from pathlib import Path
from time import monotonic
from uuid import uuid4

import httpx
from relevo.api.schemas import SubmitJob
from relevo.client import ClientSettings, RelevoClient


async def main(output):
    async with RelevoClient(
        ClientSettings(
            api_url="http://127.0.0.1:8000", api_token=os.environ["RELEVO_API_TOKEN"]
        )
    ) as client:
        job = await client.submit(
            SubmitJob(
                task_type="hash_payload", payload={"source": "observability-smoke"}
            ),
            idempotency_key=f"observability-{uuid4()}",
        )
        assert (await client.wait(job.id)).state == "succeeded"
    async with httpx.AsyncClient(timeout=5, trust_env=False) as http:
        deadline = monotonic() + 60
        while True:
            targets = (await http.get("http://127.0.0.1:9090/api/v1/targets")).json()[
                "data"
            ]["activeTargets"]
            up = {target["labels"]["job"]: target["health"] for target in targets}
            if all(up.get(name) == "up" for name in ("api", "worker", "scheduler")):
                break
            assert monotonic() < deadline, "Prometheus targets did not become healthy"
            await asyncio.sleep(0.5)
        dashboard = (
            await http.get("http://127.0.0.1:3000/api/dashboards/uid/relevo-engine")
        ).json()
        assert dashboard["dashboard"]["title"] == "Relevo engine"
        deadline = monotonic() + 30
        while True:
            now = datetime.now(UTC)
            response = await http.get(
                "http://127.0.0.1:16686/api/v3/traces",
                params={
                    "query.service_name": "relevo-worker",
                    "query.start_time_min": (now - timedelta(minutes=5)).isoformat(),
                    "query.start_time_max": now.isoformat(),
                    "query.attributes": json.dumps({"relevo.job_id": str(job.id)}),
                    "query.search_depth": 10,
                },
            )
            response.raise_for_status()
            traces = {}
            for line in response.text.splitlines():
                for resource in (
                    json.loads(line).get("result", {}).get("resourceSpans", [])
                ):
                    service = next(
                        attribute["value"]["stringValue"]
                        for attribute in resource["resource"]["attributes"]
                        if attribute["key"] == "service.name"
                    )
                    for scope in resource["scopeSpans"]:
                        for span in scope["spans"]:
                            trace = traces.setdefault(
                                span["traceId"],
                                {"services": set(), "operations": set()},
                            )
                            trace["services"].add(service)
                            trace["operations"].add(span["name"])
            found = [
                {
                    "trace_id": identifier,
                    **{key: sorted(value) for key, value in trace.items()},
                }
                for identifier, trace in traces.items()
                if {"relevo-worker", "relevo-api"} <= trace["services"]
            ]
            if found:
                break
            assert monotonic() < deadline, (
                "Worker/API distributed trace was not exported"
            )
            await asyncio.sleep(0.5)
    record = {
        "captured_at": datetime.now(UTC).isoformat(),
        "source": "scripts/smoke_observability.py",
        "job_id": str(job.id),
        "prometheus_targets": up,
        "grafana_dashboard": dashboard["dashboard"]["uid"],
        "distributed_traces": found,
        "limits": "Local transient monitoring; PostgreSQL events remain durable history.",
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    print("Monitoring smoke passed: all scrape targets, dashboard, worker/API trace.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output", type=Path, default=Path("artifacts/observability/local-smoke.json")
    )
    asyncio.run(main(parser.parse_args().output))

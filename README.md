# Relevo

**A durable task execution engine.**

Explore how jobs are claimed, retried, and recovered when workers fail.

Relevo is a backend systems portfolio project: an application submits background work, independent workers execute it, and a coordinator/recovery scheduler use PostgreSQL to track ownership and recover interrupted assignments. The focus is concurrency, transactions, failure recovery, and reproducible evidence.

## Current status

**2026-10-18: Phases 1-6 verified; Phase 7 clean-checkout/CI closeout in progress.**

All ten API endpoints, supervised workers, independent recovery, the Python client/CLI, and the failure scenarios are implemented. Separate business-effect tests demonstrate duplicate execution and transactional idempotency. Protected telemetry and optional local monitoring are verified; benchmarks are in progress. Frontend work will wait for a conversation with the user.

Verification: **196 tests passed on Windows/Python 3.13.9 and Linux/Python 3.13.16 against PostgreSQL 18.6**, including the latest server-log redaction fix and the 5 ms monitor configuration; Phase 6's 81 integration checks passed three additional rounds. Real TCP faults, worker/SQL process crashes, component restarts, and business-effect proofs have [traceable evidence](artifacts/replays/README.md). Migration `0003` adds the separate demo schema. Source is pushed to [the repository](https://github.com/Tirthpanchori/Relevo), and [hosted CI passed](https://github.com/Tirthpanchori/Relevo/actions/runs/39023521222) for the earlier `43ef7a8` checkpoint.

## Project documents

| Document | Purpose |
|---|---|
| [Implementation plan](implementation-plan.md) | Ordered tasks, phase gates, current progress, and implementation/verification evidence. |
| [Technical decisions](decision.md) | Important choices, alternatives, consequences, and how to verify them. |
| [How it works](working.md) | Plain-language explanation of jobs, workers, leases, retries, and limitations. |
| [Project memory](PROJECT_MEMORY.md) | Accepted product direction, constraints, exact HTTP routes, and scope changes. |
| [Repository instructions](AGENTS.md) | Entry instructions for agents working in this repository. |

At the start of development, read project memory, this README, the plan's current phase, and relevant decisions. Keep progress/evidence in the plan, rationale in the decision log, behavior in the working guide, and actual setup commands here.

## Intended behavior

- Save acknowledged jobs durably and deduplicate submissions with required idempotency keys.
- Atomically claim eligible work, issue expiring leases/fencing tokens, and reject stale state updates.
- Execute registered handlers in supervised child processes, with heartbeats, timeouts, and bounded output.
- Support delayed jobs, bounded retry backoff, and independently restartable recovery.
- Preserve attempt history and commit transition events with state changes.
- Demonstrate crash/network/race behavior and measure performance with 1, 3, and 5 workers.

Submission, deduplication, inspection, claims, leased ownership, supervised handler execution, fenced outcomes, expiry recovery, and committed transition history are implemented. [Repeated measurements](benchmarks/comparison.md) and [confirmation](benchmarks/confirmation.md) record actual results and limitations. The default remains a 50 ms worker monitor interval; 5 ms is optional short-task tuning, with documented timed-work regressions. Recovery may execute a handler more than once. Ownership checks reject stale state updates; external business effects need their own idempotency protection. Relevo does not claim exactly-once execution, uninterrupted uptime, or resilience to destroyed database storage. See the [working guide](working.md) for examples and boundaries.

## Agreed stack

| Area | Technology |
|---|---|
| API and validation | Python 3.13, FastAPI, Pydantic |
| Persistence | PostgreSQL 18, SQLAlchemy, Psycopg, Alembic |
| Worker runtime | Python multiprocessing, HTTPX |
| Testing and local runtime | pytest, Toxiproxy, Docker Compose |
| Observability and CI | OpenTelemetry, Prometheus/Grafana, GitHub Actions |
| Frontend, after backend verification | React, JavaScript (`.jsx`/`.js`), Vite, CSS |

Leases, claiming, scheduling, and retry/recovery coordination are implemented within Relevo. Celery, Kafka, and Kubernetes are outside v1. The agreed [ten HTTP endpoints](implementation-plan.md#http-contract-to-preserve) have [Pydantic schemas](backend/src/relevo/api/schemas.py). Exact resolved dependency versions and hashes are in [uv.lock](backend/uv.lock); runtime images are pinned by digest.

## Running and testing

Run these from the repository root with Docker Desktop running in Linux-container mode. Python is needed only for the standard-library credential generator when using the container workflow. This PC already has Python, Docker/Compose, Git, and Node.js; no additional native application is currently needed.

```powershell
python scripts/configure.py
docker compose up --build -d --wait --wait-timeout 60
```

The first command generates an ignored `.env` with private random local credentials and preserves an existing file. The second command builds the backend, starts PostgreSQL, runs migrations, and starts the API, worker, and independent scheduler. API readiness verifies schema and durability settings. Workers/schedulers have process startup checks rather than dedicated health endpoints. Services bind to localhost: API at [127.0.0.1:8000](http://127.0.0.1:8000/health/ready), interactive API documentation at [127.0.0.1:8000/docs](http://127.0.0.1:8000/docs), and PostgreSQL on port `55432`. PostgreSQL data uses a named volume mounted at the PostgreSQL 18 image's persistence location.

Run the suite against a separate ephemeral test database, not the development database:

```powershell
docker compose --profile test run --build --rm tests
```

The test service starts its own PostgreSQL instance on localhost port `55433`. Integration tests refuse database names that do not end in `_test`. The suite includes real spawned handlers and PostgreSQL transactions, competing recovery scans, worker/scheduler replacement, lost claim/report responses, rollback/commit failures, lock waits across expiry, stale-owner rejection, retry budgets, authentication, and byte limits. The test profile also starts the isolated Toxiproxy and fault API for actual TCP interruption/latency tests. Separate smoke scripts exercise container restarts and process crashes; see [Phase 6 evidence](implementation-plan.md#phase-6---failure-proof-business-effects-and-developer-tools).

For logs and a non-destructive stop:

```powershell
docker compose logs --tail 50 api worker scheduler
docker compose stop
```

Stopping preserves the development volume. Keep `.env` to reuse its credentials; changing its password does not reset an existing PostgreSQL volume. Normal startup never deletes stored jobs. Final backup/restore operations arrive in later phases.

### Optional local monitoring

```powershell
python scripts/configure_observability.py
docker compose -f compose.yaml -f infra/compose.observability.yaml --profile observability up --build -d --wait --wait-timeout 90
```

This prepares ignored local monitoring credentials and starts Prometheus at
[localhost:9090](http://localhost:9090), the provisioned Grafana dashboard at
[localhost:3000](http://localhost:3000/d/relevo-engine), and Jaeger at
[localhost:16686](http://localhost:16686). Grafana permits local anonymous viewing;
its random admin password is in `.cache/observability/grafana_password`. Do not
publish these ports. API/worker/scheduler metrics require the shared token;
Prometheus reads it from an ignored secret file. Monitoring data is temporary.

The [verified smoke](scripts/smoke_observability.py) checks all three scrape targets,
dashboard provisioning, and actual worker/API trace export. The full current
suite passes 196 tests on Windows and Linux. Durable counts/timings come from
PostgreSQL events; process counters can reset and traces can be lost. Retained
event aggregation scans history and is intended for this bounded local workload.
The [benchmark method and recordings](benchmarks/README.md) include the completed
comparison, confirmation, raw JSON/CSV, and workload-specific tuning instructions.

### Try submission from PowerShell

```powershell
$relevoToken = (Get-Content .env | Where-Object { $_ -like 'RELEVO_API_TOKEN=*' }) -replace '^RELEVO_API_TOKEN=', ''
$relevoHeaders = @{ Authorization = "Bearer $relevoToken"; 'Idempotency-Key' = 'readme-example-1' }
$relevoBody = @{ task_type = 'hash_payload'; payload = @{ message = 'Hello' } } | ConvertTo-Json -Compress
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8000/jobs -Headers $relevoHeaders -ContentType application/json -Body $relevoBody
```

The first request returns `201`; repeating the same normalized request/key returns `200` with the existing job. Different work with the same key returns `409`. A missing/malformed key or invalid task request returns `422`; the bearer token is required. Do not paste the token into frontend source or share `.env`.

Submission queues the job; the running worker executes it and reports a result. Inspect the returned job ID with `GET /jobs/{id}` and its attempts with `GET /jobs/{id}/attempts`. The internal API supports claiming (`200`, or an empty `204` when nothing is eligible), renewal, and fenced success/failure reporting. Unknown attempts return `404`; expired/incorrect ownership and conflicting reports return `409`. Renewals and accepted/exact historical reports return `200`. Claims include lease duration and result byte cap; renewals include lease duration for monotonic worker supervision.

An identical historical report returns its original acknowledgment even after a newer attempt starts or finishes. That response does not restore ownership or describe the job's latest state; inspect `GET /jobs/{id}` for current state. Heartbeats cannot revive expired leases or shorten existing ones. Transition events commit with state changes; heartbeat renewals do not add transition events.

Retryable failures and expired assignments use the job's stored total-attempt budget and configurable equal jitter: half to all of an exponential delay ceiling, default base 1 second and cap 30 seconds. Permanent failures and exhausted budgets become terminal. The scheduler scans every 2 seconds and handles at most 100 expired assignments per transaction by default. Late owner reports are rejected immediately after lease expiry, even while the scheduler is stopped. Recovery resumes from PostgreSQL when the scheduler restarts.

Payloads/results are limited to **65,536 bytes of canonical UTF-8 JSON** (sorted object keys, compact separators, unescaped Unicode, finite numbers). JSON whitespace/key order do not change a request fingerprint. Equivalent `run_at` timezones normalize to UTC; omitted/null means immediate. Accepted content keeps its identical acknowledgment if a configurable payload/result admission limit is later reduced; new over-limit work is rejected. A total raw POST-body limit of **1 MiB** applies before JSON decoding. Detailed contracts and codes are in OpenAPI.

### Source map

The public client requires `RELEVO_API_URL` and `RELEVO_API_TOKEN`. Its async methods
are `submit`, `inspect`, `attempts`, and `wait`. CLI submission requires a stable
`--key`; repeat the same request/key after an uncertain response. For a live demo
using the installed Compose image:

```powershell
docker compose exec -T api python -m relevo --api-url http://127.0.0.1:8000 demo --key readme-cli-demo
```

Use `python -m relevo --help` for submit/inspect/attempts/wait commands. The CLI
reads its token from the environment and never accepts a token argument.

| Path | Responsibility |
|---|---|
| [API](backend/src/relevo/api/app.py) / [schemas](backend/src/relevo/api/schemas.py) | HTTP routes, authentication, errors, and contracts. |
| [Submission engine](backend/src/relevo/engine/jobs.py) | Short submission transactions and inspection. |
| [Ownership engine](backend/src/relevo/engine/ownership.py) / [retry policy](backend/src/relevo/engine/retries.py) | Explicit claim/lease/report SQL, replay acknowledgments, and bounded failure retry delays. |
| [Worker supervisor](backend/src/relevo/worker/runtime.py) / [handlers](backend/src/relevo/handlers/registry.py) | Registered child-process execution, heartbeat/deadline supervision, bounded results, and exact report retries. |
| [Recovery engine](backend/src/relevo/engine/recovery.py) / [scheduler](backend/src/relevo/scheduler/__main__.py) | Independent bounded expiry scans, atomic expiry/retry events, and safe overlapping/restarted scans. |
| [Database models](backend/src/relevo/db/models.py) / [initial migration](backend/src/relevo/db/migrations/versions/0001_initial_durable_state.py) / [ownership index](backend/src/relevo/db/migrations/versions/0002_single_running_attempt.py) | Persistent state, constraints, indexes, and versioned schema. |
| [Tests](backend/tests/) | Unit and real-PostgreSQL evidence. |
| [Compose](compose.yaml) / [Dockerfile](backend/Dockerfile) | Local runtime, migration ordering, and isolated test services. |
| [CI](.github/workflows/backend.yml) | Locked dependencies, lint/format checks, and PostgreSQL tests. |

For host-based development, the local environment is `backend/.venv`; uv `0.13.1` and `backend/uv.lock` reproduce its dependencies. Container startup/testing does not require a global uv installation. Protected metrics include durable job/transition/retry/timing aggregates and runtime HTTP/database/worker telemetry. See [D025](decision.md#d025---durable-history-separated-from-bounded-runtime-telemetry) for reset, privacy, and aggregation limits.

[Worker smoke](scripts/smoke_worker.py) checks live hashing and a transient-failure retry. [Crash/recovery smoke](scripts/smoke_recovery.py) deliberately stops/restarts the local Compose worker and scheduler, checks replacement execution, and sends a stale report. With the host development environment installed, run either script from the repository root after loading `.env`:

```powershell
backend/.venv/Scripts/python.exe -c "from dotenv import load_dotenv; from runpy import run_path; load_dotenv('.env'); run_path('scripts/smoke_worker.py', run_name='__main__')"
backend/.venv/Scripts/python.exe -c "from dotenv import load_dotenv; from runpy import run_path; load_dotenv('.env'); run_path('scripts/smoke_recovery.py', run_name='__main__')"
```

The crash check expects the default 15-second lease and a development Compose instance. It creates a timed demo job and restores both services in cleanup. The scripts do not print the API token.

## Frontend and deployment

The frontend will explain the architecture and guarantees, replay actual recorded failure tests, show attempt timelines, and present measured benchmark results. It is an explanatory portfolio experience. Replay will be clearly labeled and traceable to its tests; the public bundle will contain no privileged API token.

Deployment is **free-only: INR 0 recurring budget**. GitHub Pages is the proposed static frontend host. An optional live engine depends on verified ongoing free capacity; local Compose and recorded evidence remain the fallback. Paid hosting, paid databases/domains, and time-limited credits are outside scope. No live URL is available yet.

## Next step

Complete [Phase 7](implementation-plan.md#phase-7---observe-benchmark-and-close-the-backend-gate): observability, measured workloads, one verified improvement, and the backend gate. Discuss frontend direction with the user before Phase 8.

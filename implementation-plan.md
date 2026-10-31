# Relevo implementation plan

Created: 2026-10-16 (Asia/Calcutta). Build order: **backend, then frontend**.

## How to use this plan

This is the execution checklist for the whole build. Read [PROJECT_MEMORY.md](PROJECT_MEMORY.md) and the relevant entries in [decision.md](decision.md) before changing the design. Follow [design.md](design.md) alongside this plan for frontend structure and the visual direction, distinguishing its proposals from accepted decisions. Use [working.md](working.md) for the plain-language explanation and [README.md](README.md) for the project entry point.

- Work through the phases in order. Tests for a guarantee belong in the phase that introduces it.
- Keep task IDs stable. Mark a task complete only when its deliverable exists and its completion checks pass.
- When closing a phase, add the actual implementation paths, verification commands, and results to its evidence field. A plan or a manual observation alone is not proof of a concurrency guarantee.
- Record important tradeoffs in `decision.md` in the same change. Update `working.md` when behavior changes, `README.md` when setup changes, and project memory when scope or a milestone changes.
- Do not begin frontend implementation until the backend gate in Phase 7 passes. Writing API contracts and capturing evidence are backend work.

## Scope and current progress

Relevo is a durable task execution engine for demonstrating concurrency, transactions, coordination, recovery, and measured performance. The target effort is 6-8 weeks at 10-15 hours per week. Deployment has a recurring budget of **INR 0**. Phase gates take priority over calendar estimates.

Indicative allocation: weeks 1-2 for Phases 1-3, weeks 3-4 for Phases 4-5, weeks 5-6 for Phases 6-7, and weeks 7-8 for Phases 8-9. Reassess after each gate; if backend correctness takes longer, move frontend work later rather than reducing failure coverage.

| Phase | Deliverable | Status |
|---|---|---|
| 0 | Scope, decisions, working guide, and implementation checklist | Complete: documentation baseline |
| 1 | Backend skeleton, API contract, migrations, and CI | Complete: local and hosted CI |
| 2 | Durable, idempotent submission and inspection | Complete |
| 3 | Atomic claims, leases, and fenced outcomes | Complete |
| 4 | Supervised worker runtime and registered handlers | Complete |
| 5 | Delayed execution, retries, and independent recovery | Complete |
| 6 | Fault tests, business-effect demonstration, Python client/CLI | Complete: local and hosted CI |
| 7 | Telemetry, benchmarks, and backend readiness gate | Complete: backend gate passed |
| 8 | Explanatory React frontend using recorded evidence | Design discussion: draft information architecture; UI not started |
| 9 | Reproducible packaging and free deployment | Planned |

**Phases 1-7 are complete; the backend readiness gate passed on 2026-10-18.** The final code checkpoint passes 197 tests on Windows/Linux, a fresh-checkout 197-test run, and [hosted CI](https://github.com/Tirthpanchori/Relevo/actions/runs/39067364211). Phase 6's 81 integration checks also passed three additional rounds. Real crash/restart/effect evidence, protected monitoring/traces, 1,440 retained benchmark jobs, and an explicitly limited tuning option are recorded below. Frontend and cloud deployment have not begun. Have the required frontend conversation before Phase 8.

### V1 boundaries

Include immediate/delayed jobs, three total attempts by default, lease renewal, stale-owner rejection, a durable attempt/event history, three demonstration handlers, a Python client/CLI, and failure evidence. Use the stack recorded in [project memory](PROJECT_MEMORY.md#technology-direction).

Exclude Celery, Kafka, Kubernetes, uploaded executable code, workflow graphs, recurring cron schedules, multi-tenancy, a graphical administration dashboard, and resetting terminal jobs. External adoption is not an acceptance criterion. A portfolio explanation with a replay is part of v1.

## Phase 0 - Establish the baseline

- [x] P0.1 Preserve the accepted scope, stack, exact HTTP routes, engine guarantees, and free-only budget in project memory.
- [x] P0.2 Create this ordered checklist, the technical decision log, the simple working guide, and README.
- [x] P0.3 Link the documents from the repository instructions so later sessions know where to resume.

**Completion check:** the four requested documents agree with project memory, distinguish plans from implementation, and identify the next backend step.

**Evidence:** [AGENTS.md](AGENTS.md), [PROJECT_MEMORY.md](PROJECT_MEMORY.md), [decision.md](decision.md), [working.md](working.md), and [README.md](README.md). Documentation review only; no engine checks have run.

Baseline validation: all four documents are nonempty; 39 local links/heading anchors resolve; all 53 task IDs are unique; all ten agreed HTTP routes appear in the plan; code fences are balanced. These checks validate documentation structure, not engine behavior.

## Phase 1 - Backend foundation and contracts

- [x] P1.1 Initialize Git if the workspace is still unversioned; add ignore rules and a Python 3.13 project with a repeatable dependency installation. Pin compatible dependency versions when installing them.
- [x] P1.2 Scaffold `backend/src/relevo/` with `api`, `engine`, `db`, `worker`, `scheduler`, `handlers`, and `client` boundaries; add `backend/tests/`. Keep HTTP validation out of engine operations and task execution out of API processes.
- [x] P1.3 Add typed environment configuration and a secret-free example environment file. Include database URL, shared API token, timing/size/retry limits, and finite HTTP/database timeouts. Validate heartbeat/lease timing combinations on startup.
- [x] P1.4 Create Compose services for PostgreSQL 18 and the API, with a persistent database volume and a separate migration command. Add worker and scheduler services in their phases; put fault/telemetry tools in optional profiles.
- [x] P1.5 Specify Pydantic request/response schemas and errors for all ten routes below. Define job/attempt IDs, UTC timestamps, `Idempotency-Key`, worker identity, fencing token, normalized reports, and the distinction between retryable failure and permanent failure.
- [x] P1.6 Implement Alembic migrations for `jobs`, `attempts`, and `job_events`, with foreign keys, state constraints, unique submission keys, unique per-job attempt numbers/tokens, and ordered per-job events. Add indexes for eligible pending work and expired running attempts. Keep the business-effect ledger separate until Phase 6.
- [x] P1.7 Add liveness/readiness and baseline GitHub Actions checks: formatting/linting, unit tests, migrations against real PostgreSQL, and integration tests as they are introduced. Liveness checks the process; readiness checks database access and schema readiness without leaking configuration.

**Completion check:** a fresh database migrates to head, the API starts, OpenAPI describes the agreed routes, readiness fails cleanly without a usable database/schema, configuration errors fail clearly, and the configured CI checks reproduce the baseline locally. Hosted CI execution must also be verified after a GitHub remote exists. Unimplemented operations must not advertise successful execution.

**Evidence (2026-10-16):** [Python project/lock](backend/pyproject.toml), [configuration](backend/src/relevo/config.py), [contracts/API](backend/src/relevo/api/app.py), [migration 0001](backend/src/relevo/db/migrations/versions/0001_initial_durable_state.py), [Compose](compose.yaml), [CI workflow](.github/workflows/backend.yml), and [tests](backend/tests/). `docker compose up -d --wait --wait-timeout 60` reached healthy readiness; `docker compose --profile test run --rm tests` passed all 47 checks on Linux/Python 3.13.16/PostgreSQL 18.6. The same suite passed on Windows/Python 3.13.9. Ruff lint/format and Alembic round-trip/drift checks passed. Hosted CI has not run; no remote is configured. Worker/scheduler/fault/telemetry services remain assigned to later phases.

### HTTP contract to preserve

These methods and paths are agreed. The behavior below is the contract to implement and test; it does not describe existing endpoints.

| Method and path | Behavior |
|---|---|
| `POST /jobs` | Persist a registered task and required idempotency key; return only after commit. Identical replay returns the same job; changed content with the same key returns `409`. |
| `GET /jobs/{id}` | Return a job's current state, scheduling information, and final result/error when available. |
| `GET /jobs/{id}/attempts` | Return execution attempts in stable attempt order. |
| `POST /internal/claim` | Atomically assign one eligible job to a worker, or return a documented no-work response. |
| `POST /internal/attempts/{id}/heartbeat` | Renew only the current, unexpired ownership. |
| `POST /internal/attempts/{id}/complete` | Commit a fenced success, or acknowledge an identical previously committed report. |
| `POST /internal/attempts/{id}/fail` | Commit a fenced failure/retry decision, or acknowledge an identical previously committed report. |
| `GET /health/live` | Report process liveness. |
| `GET /health/ready` | Report whether the API can safely serve database-backed operations. |
| `GET /metrics` | Expose operational metrics on the trusted monitoring boundary. |

Protect job routes, internal routes, and metrics with the environment-provided shared bearer token or private monitoring access as appropriate. Health responses expose only minimal status. Do not put the shared token in browser code. In job routes `{id}` means a job; in internal routes it means an attempt. The [schemas](backend/src/relevo/api/schemas.py) and [HTTP responses](backend/src/relevo/api/app.py) implement: new/replayed submissions `201`/`200`, conflict `409`, missing job/attempt `404`, invalid/missing request fields `422`, unauthorized `401`, oversized payload/result/raw body `413`, and unconfirmed database operation `503`. Claims use `200`/`204` for assigned/no eligible work; expired/stale/incorrect ownership and conflicting reports use `409`. Renewals and accepted/identical historical reports return `200`. No internal operation returns a placeholder `501` anymore.

## Phase 2 - Durable submission and inspection

- [x] P2.1 Implement canonical request normalization and fingerprints. Include all task-affecting submission fields. Distinguish an immediate request from an explicit `run_at`; never put a newly generated timestamp into the fingerprint of an immediate request. Validate registered task names, timezone-aware dates, and serialized payload size.
- [x] P2.2 Implement transactional submission with a database-enforced unique idempotency key. Resolve racing inserts transactionally; the same normalized request returns the existing job and different content returns a conflict. Commit the submission event with the job.
- [x] P2.3 Implement job status and ordered attempt-history reads. Keep the original submission immutable; retain the idempotency binding for the lifetime of the job in v1.
- [x] P2.4 Verify normal submission, sequential/concurrent duplicates, changed payload/schedule conflicts, equivalent normalized requests, invalid/oversized requests, missing jobs, and rollback on database failure. Assert one job and one submission event for concurrent duplicates.
- [x] P2.5 Verify the uncertain-response case: commit a submission, lose its response, and retry with the same key. Track acknowledged job IDs for later crash-accounting assertions.

**Completion check:** no success is returned before commit; retries resolve uncertainty without creating another job; a job and its submission history cannot partially commit.

**Evidence (2026-10-16):** [submission engine](backend/src/relevo/engine/jobs.py), [serialization](backend/src/relevo/engine/serialization.py), [submission integration tests](backend/tests/integration/test_submission.py), [HTTP checks](backend/tests/unit/test_http_contract.py), and [live smoke script](scripts/smoke.py). The passing suite covers eight synchronized duplicate submitters, racing conflicting payloads, timezone/key-order normalization, rollback before event persistence, injected commit failure, a discarded response after commit, exact UTF-8 byte boundaries, and invalid/unavailable requests. The lost-response case uses a controlled client-transport failure; proxy/network crash scenarios remain in Phase 6. Acknowledged IDs are asserted against durable rows. The live smoke check also passed against Compose without disclosing credentials.

## Phase 3 - Atomic ownership and fenced reports

- [x] P3.1 Implement explicit SQL claims with `FOR UPDATE SKIP LOCKED`, deterministic candidate ordering, short transactions, and eligibility checked against database time. Create the attempt, increment the per-job fencing token, set the lease, and record the transition in one transaction.
- [x] P3.2 Use a consistent lock order across claims, heartbeats, reports, and recovery. Serialize ownership changes on the job row; revalidate the current attempt/token/worker and fresh database time after acquiring locks. A transaction's start timestamp must not validate a lease after a lock wait.
- [x] P3.3 Implement heartbeat renewal, completion, and failure with the same ownership rules. An expired lease cannot be renewed or used for a new outcome even if recovery has not scanned it yet.
- [x] P3.4 Persist enough normalized outcome data to recognize an identical already-committed completion/failure report. An exact replay by the matching attempt identity returns its original outcome without changing current job state, consuming another attempt, or adding another transition. Conflicting reports are rejected.
- [x] P3.5 Test competing claimers, unknown/wrong worker identities and tokens, expiration boundaries, heartbeat-versus-expiry races, complete-versus-fail races, and repeated reports. Include a lock-wait test that crosses lease expiry.

**Completion check:** each claim has one atomic job/attempt/event record; concurrent callers never create two valid owners; only a valid owner can commit a new transition; identical report replays are harmless.

**Evidence (2026-10-16):** [ownership SQL](backend/src/relevo/engine/ownership.py), [migration 0002](backend/src/relevo/db/migrations/versions/0002_single_running_attempt.py), [ownership tests](backend/tests/integration/test_ownership.py), [HTTP/lost-report-response tests](backend/tests/integration/test_worker_http.py), and [retry policy tests](backend/tests/unit/test_retries.py). All 103 checks pass on Windows/Python 3.13.9 and Linux/Python 3.13.16 against PostgreSQL 18.6. Verified with `uv run --project backend --env-file .env --no-sync python -m pytest backend/tests -q` and `docker compose --profile test run --rm tests` (this PC's uv executable is `.tools/Scripts/uv.exe`). Nine checks selected by `pytest backend/tests/integration/test_ownership.py -q -k 'competing or concurrent_identical or lock_wait or many_workers'` passed in five consecutive runs (45 race-check executions).

These checks cover claim contention/ordering, the database's single-running-attempt constraint, atomic rollback, heartbeat/report serialization, expiry at lock/write boundaries, wrong/old identities, exact and conflicting report replays, lost report responses, bounded result sizes, and acknowledgment replay after configuration changes. The installed runtime image starts with schema `0002` and reaches healthy readiness. No task handler was executed by these coordination tests; reports are controlled test inputs. The Phase 5 scheduler must reuse this lock order, and actual recovery races/crashes remain unverified until that process exists.

## Phase 4 - Supervised worker execution

- [x] P4.1 Build an HTTPX worker loop that claims one job at a time, backs off when idle/unavailable, and identifies each worker process instance. Keep coordinator calls bounded by timeouts.
- [x] P4.2 Run registered handlers in a supervised child process with a Windows/Linux-compatible process start method. Keep connections process-local and protect entry points. Send only bounded handler input/output over process communication.
- [x] P4.3 Renew ownership from the supervisor while the child executes. Terminate and reap the child on rejected ownership, unconfirmed renewal, or task timeout. Bound shutdown and document what happens when the supervisor itself is abruptly killed.
- [x] P4.4 Implement payload hashing, timed work, and configured transient-failure handlers. Enforce result-size limits before reporting. Treat handler exceptions and execution timeout through documented failure rules.
- [x] P4.5 Retry ambiguous completion/failure delivery using the same normalized report. Never execute the handler again merely because a report response disappeared. A lost claim response must lead to eventual lease recovery without unsafe speculative execution.
- [x] P4.6 Add worker Compose services and tests for successful execution, handler failure, oversized output, timeout, ownership loss, blocked renewal, child cleanup, and process restart.

**Completion check:** a worker completes jobs end to end, supervises rather than blocks on task execution, and stops local execution when ownership cannot be confirmed. Tests do not assume an abruptly killed supervisor can always stop an orphan instantly.

**Implementation (2026-10-16):** [HTTPX client](backend/src/relevo/worker/coordinator.py), [supervisor](backend/src/relevo/worker/runtime.py), [spawn-safe child](backend/src/relevo/worker/child.py), [CLI](backend/src/relevo/worker/__main__.py), [registered handlers](backend/src/relevo/handlers/registry.py), and worker service in [Compose](compose.yaml). Claims/renewals include lease duration; claims include the result byte cap. The worker uses request-start-based monotonic deadlines, total async HTTP timeouts, atomic bounded-file IPC, child termination/reaping, identical report retries, and a best-effort parent-death watchdog. Worker configuration needs only coordinator access, not a database URL.

**Verified locally:** 137 tests passed on Windows/Python 3.13.9 (19.77 seconds) and Linux/Python 3.13.16 (13.27 seconds), using real PostgreSQL 18.6. [Worker checks](backend/tests/unit/test_worker.py) cover real spawned execution, explicit handler failures, output bounds, timeout, lost/rejected heartbeat, cleanup, shutdown, total HTTP deadlines, and identical lost-report retries. [Worker integration](backend/tests/integration/test_worker_execution.py) proves real handler/API/database completion and a failed attempt followed by success. Its additional targeted lost-claim test now proves a committed-but-unreceived claim is never executed speculatively and completes through scheduler recovery plus a replacement worker.

`docker compose up --build -d --wait --wait-timeout 60` passed with the worker. [Installed worker smoke](scripts/smoke_worker.py) verified canonical hashing and an actual transient failure/retry over HTTP, then passed again after `docker compose restart worker`; the worker identity changed. Ruff lint/format, Compose syntax, and worker CLI help pass.

**Limits:** the earlier automatic approval usage block cleared and the checks above ran through approved execution. No manual user test run is now needed. Isolated supervisor death/orphan timing is still a best-effort implementation, not a universal instantaneous-stop guarantee. Broader proxy/network/process-failure evidence belongs to Phase 6.

## Phase 5 - Delays, bounded retries, and independent recovery

- [x] P5.1 Implement delayed eligibility through `run_at`/`available_at`. Delayed jobs remain `pending`; workers never claim them early. Use database time, not worker clocks.
- [x] P5.2 Define configurable bounded exponential backoff and jitter, with injectable randomness for deterministic tests. Default to three total attempts, including the first. Permanent failures and exhausted budgets become terminal.
- [x] P5.3 Build an independently restartable scheduler that scans expired leases in bounded batches and locks/revalidates before changing ownership. Close the expired attempt and either schedule a retry or fail the job atomically with its events.
- [x] P5.4 Make multiple overlapping recovery scans safe. A scheduler interruption or restart must neither lose work nor double-count an expiry/retry. Do not run recovery only inside an API startup hook.
- [x] P5.5 Add the scheduler Compose service and tests for delay boundaries, retry availability, jitter bounds, exhausted budgets, poison-job isolation, recovery-versus-heartbeat/completion races, and scheduler outage/restart.

**Completion check:** kill a worker after claim, expire its lease, and complete the job through another attempt; reject the old attempt's late outcome. Stop/restart the scheduler and observe recovery resume from persisted state.

**Evidence (2026-10-16):** P5.1/P5.2 were prerequisites of Phase 3. See [ownership tests](backend/tests/integration/test_ownership.py), [policy tests](backend/tests/unit/test_retries.py), and [D018](decision.md#d018---persisted-outcome-acknowledgments-and-positive-retry-jitter). The [recovery engine](backend/src/relevo/engine/recovery.py), [independent scheduler](backend/src/relevo/scheduler/__main__.py), and [recovery checks](backend/tests/integration/test_recovery.py) now pass the full PostgreSQL suite: **152 tests on Windows/Python 3.13.9 (30.56 seconds) and Linux/Python 3.13.16 (16.07 seconds)**. Tests cover bounded batches, six concurrent scanners closing 15 expiries once, lock skipping/revalidation, rollback at event/commit boundaries, expiry budgets, stale-owner races, fresh scheduler subprocesses, and real worker completion after a lost claim response. Defaults: 2-second scans, at most 100 expiries per transaction, and the existing positive jitter policy.

Six new recovery concurrency/rollback checks also passed **five consecutive rounds (30 executions)** using `pytest backend/tests/integration/test_recovery.py -q -k "overlapping_scans or recovery_races or revalidates or interrupted_scan"`. The earlier nine Phase 3 race checks retain their separately recorded five-round evidence.

`docker compose up --build -d --wait --wait-timeout 60` passes with API, worker, and scheduler. [Installed crash/recovery smoke](scripts/smoke_recovery.py) passed for job `b90bb8c2-a417-4177-9a69-6aaf32968006`: stop scheduler; observe claimed timed work; send `SIGKILL` to the worker container; start a new worker; observe the job still running past the old lease while recovery is stopped; restart scheduler; observe attempts `expired,succeeded` with a higher token and different worker; reject the original attempt's late report with `409`. Services are restarted in the script's cleanup. This proves the described local process/container scenario; it does not complete the Phase 6 network/storage/business-effect matrix or isolated orphan timing proof.

## Phase 6 - Failure proof, business effects, and developer tools

- [x] P6.1 Add real-PostgreSQL integration scenarios for every row in the failure matrix below. Use barriers, observable checkpoints, controlled database deadlines, and bounded polling. Avoid arbitrary sleeps as race-test synchronization.
- [x] P6.2 Use Toxiproxy for controlled connection interruption/latency and instrumented test checkpoints for precise commit-then-lost-response cases. Record exactly which process or connection each scenario interrupts.
- [x] P6.3 Add a separate demonstration business-effect ledger. First show repeated effects after an effect commits but completion is lost. Then protect the business operation with a stable business idempotency key and a unique constraint in the same transaction as the effect. An attempt ID is not a stable business key across retries.
- [x] P6.4 Build the small Python client and CLI for submit, inspect, attempts, and reproducible demos. Require explicit API URL/token configuration; retry submission with its original key. Make the engine demonstrable without a browser.
- [x] P6.5 Capture sanitized actual committed events and test observations for worker death/recovery, stale-report rejection, and the effect-idempotency comparison. Store scenario, source test/script, configuration, schema version, capture date, and implementation revision with each recording. Do not fabricate replay events.
- [x] P6.6 Run the failure suite repeatedly with bounded completion criteria. Assert that every acknowledged job remains in a valid state, terminal outcomes do not change, attempt budgets hold, and transition history agrees with current state.

| Failure scenario | Required observation |
|---|---|
| Concurrent duplicate submissions | One durable job; mismatching content conflicts. |
| Several workers compete | One valid lease per job; distinct atomic attempts. |
| Claim commits but its response disappears | Unexecuted ownership eventually expires and is recovered within the retry policy. |
| Worker dies after claim | The job stays accounted for and a later eligible attempt can recover it. |
| Heartbeats are interrupted | The supervisor stops the child; an unrenewed lease expires. |
| Old worker reports after expiry/reassignment | Its new outcome is rejected, even before the next scheduler scan. |
| Submission response disappears after commit | Retrying the same key returns the original job. |
| Completion/failure response disappears after commit | Identical report replay changes no state or history; conflicting replay is rejected. |
| Database disconnects or restarts | No false acknowledgment; previously acknowledged jobs survive restart with the persistent volume. |
| Coordinator restarts | Persisted jobs/leases remain authoritative; reconnect/recovery follows the lease rules. |
| Scheduler stops/restarts or scans overlap | Recovery resumes; expired attempts are closed only once. |
| A job is delayed | No attempt starts before eligibility. |
| A poison job exhausts its attempts | It becomes failed; healthy jobs continue. |
| Effect commits before completion is lost | Execution can repeat; a business idempotency constraint prevents the protected duplicate effect. |

**Completion check:** the matrix has passing, repeatable scenarios linked to tests; the CLI can run the core demonstration; recordings are traceable to real execution. Restart tests establish process-crash behavior, not resilience to destroyed storage.

**Evidence (2026-10-17):** [public async client/CLI](backend/src/relevo/client/), [client checks](backend/tests/unit/test_client.py), [public-client integration](backend/tests/integration/test_public_client.py), [effect transaction](backend/src/relevo/demo/effects.py), [effect tests](backend/tests/integration/test_effects.py), [additive demo migration](backend/src/relevo/db/migrations/versions/0003_demo_ledger.py), [real TCP fault tests](backend/tests/integration/test_network_faults.py), and [cross-table accounting](backend/tests/accounting.py). The full Phase 6 suite passed **185 tests on Windows/Python 3.13.9 (47.85 seconds) and Linux/Python 3.13.16 (29.01 seconds)**. On 2026-10-17 the **81 integration checks passed three more consecutive rounds (243 executions: 35.56/30.09/30.44 seconds)**, with accounting checks after every PostgreSQL test.

[Component restart smoke](scripts/smoke_restarts.py) proved API stop/restart, unavailable-database rejection, normal PostgreSQL restart, and PostgreSQL `SIGKILL` recovery on the surviving named volume; pending and terminal acknowledged jobs survived unchanged and the pending job subsequently completed. [Worker crash smoke](scripts/smoke_recovery.py) again passed with real worker `SIGKILL`, scheduler outage/restart, replacement success, and stale completion `409`. The installed CLI's `demo --key phase6-cli-installed-demo` also completed through a real worker.

Traceable captures and reproduction commands are in [artifacts/replays](artifacts/replays/README.md). Business-effect recordings use an explicitly instrumented hashing/business-transaction harness; they do not grant database credentials to registered child handlers. Forced test lease expiry is labeled in observations. TCP tests block the test API's downstream responses, disable the test database proxy, or delay heartbeat replies; development links are separate. [CI](.github/workflows/backend.yml) now runs the Compose fault suite. Hosted execution remains pending until the user creates/connects the repository.

## Phase 7 - Observe, benchmark, and close the backend gate

- [x] P7.1 Add structured logs with job, attempt, worker, token, and transition identifiers. Redact tokens and avoid logging full payloads/results. Keep high-cardinality IDs out of Prometheus labels.
- [x] P7.2 Add OpenTelemetry traces for coordinator/engine operations and Prometheus metrics for queue delay, execution duration, retries, expired leases, stale reports, API/database latency, and current job states. Provide optional local Prometheus/Grafana configuration.
- [x] P7.3 Treat PostgreSQL events as durable history; process counters/traces can miss observations or reset on restart. Separate event-derived totals from runtime telemetry in reports.
- [x] P7.4 Benchmark identical short/long workloads with 1, 3, and 5 workers. Record warmup, repeated runs, workload/handler parameters, hardware, configuration, dependency versions, revision, raw measurements, throughput, queue delay, API latency percentiles, CPU/memory, and database contention. Keep durability settings unchanged.
- [x] P7.5 Identify one measured bottleneck, make a bounded improvement, rerun the same workload, and publish before/after results with limitations. Preserve correctness tests; do not assume worker count produces linear scaling.
- [x] P7.6 Run the backend gate below and update this plan, the decision log, working guide, README, and memory with actual evidence.

**Observability evidence (2026-10-17):** [runtime telemetry](backend/src/relevo/observability.py), [durable collector](backend/src/relevo/observability_db.py), [integration checks](backend/tests/integration/test_observability.py), [monitoring overlay](infra/compose.observability.yaml), and [actual smoke capture](artifacts/observability/local-smoke.json). Full suites passed **195 tests on Windows/Python 3.13.9 (49.33 seconds) and Linux/Python 3.13.16 (32.08 seconds)**, including real TCP faults. [Monitoring smoke](scripts/smoke_observability.py) verified healthy API/worker/scheduler targets, the provisioned Grafana dashboard, and a distributed worker/API trace. [D025](decision.md#d025---durable-history-separated-from-bounded-runtime-telemetry) records timing, privacy, restart, and retained-history scan limits. Benchmark/CI verification was pending at this checkpoint; see the subsequent milestones below.

**Baseline evidence (2026-10-18):** [completed raw matrix](benchmarks/raw/baseline-complete.json) contains all 18 cases: two fixed workloads × 1/3/5 workers × three repetitions, thirty measured jobs plus ten warmup jobs per case (540 measured jobs). Every retained case passed result/ID/single-attempt/fencing/history checks and includes resource/database samples and API latency. Normal PostgreSQL durability remained enabled. [Method and excluded runs](benchmarks/README.md) preserve the sampling pilot, unexpected expiry/recovery, and bounded timeout separately. The final three cases resumed only after verifying unchanged runtime source/image/configuration; harness revisions are recorded. P7.5's 5 ms monitor candidate remains unverified and the default stays 50 ms.

**Candidate/correctness checkpoint (2026-10-18):** [repeated comparison](benchmarks/comparison.md) and [job CSV](benchmarks/comparison.csv) derive from two complete 18-case matrices (1,080 measured jobs). [Experiment notes](benchmarks/experiment-notes.md) retain the observed five-worker timed regression, session/background-load confounders, and CPU tradeoffs. The final audit fixed a demonstrated Uvicorn-handler redaction bypass. With the candidate 5 ms configuration, the full updated suite passes **196 checks on Windows (36.72 seconds) and Linux (28.83 seconds; 84% statement coverage, with subprocess coverage limitations)**. Source default remains 50 ms pending a further same-image baseline/candidate confirmation and clean-checkout gate.

**Optimization decision (2026-10-18):** [same-image confirmation](benchmarks/confirmation.md) adds twelve cases/360 measured jobs to the repeated matrices. The 5 ms option improves the single-worker short workload from 3.103 to 4.001 jobs/s in confirmation (+28.9%), but timed-work throughput regresses. [D026](decision.md#d026---bounded-measurement-and-worker-monitor-experiment) therefore retains the 50 ms default and exposes validated 5 ms tuning through worker configuration/Compose. This is a measured workload-specific option, not a blanket speedup. Windows sleep interrupted an excluded confirmation; [recorded power events](artifacts/verification/host-power.json) explain that pause. The successful confirmation used a process-scoped idle-sleep request without changing the power plan. Clean-checkout verification and final CI/documentation closeout remain.

### Backend gate - all items required before Phase 8

- [x] Durable submission, deduplication, claims, leases, fencing, delayed eligibility, bounded retries, and recovery have passing real-PostgreSQL tests. See Phases 2-6 and the final 197-test Windows/Linux checkpoint below.
- [x] Every failure-matrix scenario passes repeatedly; acknowledged-job accounting and history consistency are asserted. See Phase 6's 243 additional integration executions and [accounting checks](backend/tests/accounting.py).
- [x] Business-effect duplication and its idempotent alternative are demonstrated separately from executor-state fencing. See [effect tests](backend/tests/integration/test_effects.py) and [actual captures](artifacts/replays/README.md).
- [x] API, worker, and scheduler restart independently; client/CLI demos work; documented Compose startup works from a clean checkout. See the [197-test fresh-checkout capture](artifacts/verification/clean-checkout.json), [restart capture](artifacts/replays/component-restarts.json), and [worker crash capture](artifacts/replays/worker-crash-recovery.json).
- [x] CI runs the essential integration/recovery suite with no credentials in source or fixtures. [Hosted run 39067364211](https://github.com/Tirthpanchori/Relevo/actions/runs/39067364211) passed for `9af3ab8`; [sanitized evidence](artifacts/verification/hosted-ci.json) records the verified SHA/steps. Staged secret review passed.
- [x] Metrics, raw benchmark measurements, methodology, one measured optimization, and traceable replay recordings exist. See [monitoring capture](artifacts/observability/local-smoke.json), [benchmark method/reports](benchmarks/README.md), [installed tuning check](artifacts/verification/worker-tuning.json), and [replays](artifacts/replays/README.md).
- [x] Published wording matches tested guarantees and explains downtime, retry exhaustion, duplicated execution, and storage-loss limits. See [working guide](working.md), [README](README.md), and D025-D027; no universal speedup or fixed recovery-attempt count is claimed.

**Completion check:** each checked item links to its implementation and evidence. Any failed item keeps the gate open.

**Final gate evidence (2026-10-18):** code checkpoint `9af3ab8` passes **197 checks on Windows/Python 3.13.9 (39.23s), Linux/Python 3.13.16 (29.25s), and a fresh committed checkout (197 tests, 27.80s)** against PostgreSQL 18.6/schema `0003`. Fresh credentials reject the old token; installed CLI jobs succeed before/after restart, saved terminal data/history stay identical, and the worker identity changes. Verification containers/network/new volume were removed and development storage/services restored. Hosted CI passes the same essential container/fault suite.

Refreshed actual captures against `9af3ab8` prove worker SIGKILL/replacement/stale rejection and API/PostgreSQL restart/SIGKILL survival. The stronger crash harness checks bounded expired prefixes, contiguous tokens/numbers, every old owner's rejection, immutable terminal state, and matching committed history. The earlier extra-expiry run remains an explicitly labeled diagnostic (D027). Final monitoring verifies all three scrape targets, dashboard provisioning, and worker/API trace export. The optional 5 ms Compose setting ran a real CLI job successfully and was restored to 50 ms. Repeated/confirmation reports retain raw timings, source/image metadata, resource samples, regressions, and revision-specific limitations. No frontend or cloud deployment was started.

## Phase 8 - Build the explanatory frontend

Depends on the complete Phase 7 gate. Use React, JavaScript (`.jsx`/`.js`), Vite, and CSS.
The user explicitly requested a conversation before frontend work (2026-10-17).
That discussion happened on 2026-10-18: page structure, merged Engine/Replay,
references, palette, fonts, original animation approach, and stack were reviewed.
The user then explicitly authorized implementation. Phase 8 is now in progress.

- [x] P8.1 Establish the visual direction, information hierarchy, responsive layout, and accessible interaction model before UI implementation. Keep the product an explanation of the engine and its evidence.
- [x] P8.2 Build the introduction, developer use cases, architecture explorer, lifecycle explanation, guarantees/limitations, quickstart, and repository links. Include the accepted Griffin-inspired pixel/ASCII motif using Relevo's original pattern and design tokens. Include the grouped footer with `llms.txt` and Sitemap (`sitemap.xml`) links under About; prepare factual static utility-file contents alongside the public pages.
- [x] P8.3 Build the Engine page's Replay tab with clearly labeled actual recorded tests: worker failure, lease expiry, recovery, stale-report rejection, and attempt timeline. Share the workspace with the Flow tab, show one active panel/scenario, and pause hidden playback. Expose the capture metadata/source and distinguish explanatory annotations from recorded events. Support play/pause, restart, and stepping without requiring animation.
- [x] P8.4 Present actual benchmark results with hardware, workload, methodology, and limitations. Omit unmeasured numerical claims. Keep replay data and site navigation independent of live engine availability.
- [x] P8.5 Verify keyboard controls, tab/focus behavior, direct links to Flow/Replay, hidden-playback pause, contrast, reduced motion, narrow layouts, static diagram comprehension, and Vite production build. Check the decorative pixel/ASCII effect's pause/static modes, offscreen/hidden rendering suspension, text readability, and bounded mobile cost. Validate the footer utility links, readable/factual `llms.txt`, and well-formed sitemap with the intended canonical public page set. Ensure the published bundle contains no shared API token or privileged live controls.

**Completion check:** a visitor can explain a job's lifecycle and the failure/recovery evidence without running the backend. The site remains useful when the live engine is offline.

**Evidence:** design conversation started 2026-10-18. Reference roles: [Cierto](https://cierto-beta.vercel.app/) for structure/supporting pages/light-dark blocks, [Griffin](https://www.griffin.com/) for breakdown/design inspiration, [Etched](https://www.etched.com/) for schematic footer artwork. Choose Relevo's own colours. References inspected in the browser. The user accepted merging Engine and Replay into one page with Flow/Replay tabs; [D028](decision.md#d028---one-engine-page-with-flow-and-replay-tabs) records the rationale. [design.md](design.md) now proposes six total content pages plus a not-found view, an Engine/Results/Docs header plus GitHub, and Product/Evidence/Build/About footer groups with Replay linking to `/engine/#replay`. The merge/tab model is accepted; remaining scope, palette, compositions, final accessible/responsive interaction model, and UI verification are pending. P8.1 is not complete.

**LLM content checkpoint (2026-10-18):** [llms.txt](llms.txt) now exists as a repository source draft matching the user's Cierto screenshot: title, summary, key facts, and grouped descriptive Docs/Evidence/Results/Project/Optional links. It uses existing repository resources and labels the website as unbuilt. Source-link paths and dated verification references are checked locally; frontend publication, sitemap, final site URLs, and P8.2/P8.5 completion remain pending.

**Walkthrough checkpoint (2026-10-18):** `design.md` now elaborates the proposed visitor journey, page/workspace layouts, and mobile/motion/loading/error behavior for the user's requested review. These are planning details, not visual approval or implemented UI. Palette/type/final compositions remain open; no P8 task is marked complete by this walkthrough.

**Palette proposal (2026-10-18):** `design.md` records a warm chalk/graphite/burnt-orange recommendation and semantic state colours. Fourteen intended opaque text/surface pairs were calculated (minimum 4.81:1). A conversation preview displays the proposed light/dark colours; this is design evidence only. User acceptance and final rendered UI checks remain pending; P8.1/P8.5 stay open.

**Pixel/ASCII direction (2026-10-18):** the user accepted Griffin's pixelated landing-page motif. Browser inspection confirms its ASCII-pattern canvas banner. `design.md` records the accepted motif and proposed original Relevo treatment: a hero-edge band, sparse transitions, decorative labeling/meaning, pause/static modes, and bounded rendering. Exact layout, renderer, motion, palette acceptance, implementation, and checks remain pending; no P8 task closes from this design choice.

**Implementation checkpoint (2026-10-18):** the user authorized the reviewed
direction and original SVG/Canvas implementation. [PRODUCT.md](PRODUCT.md),
[the pre-build direction contract](artifacts/design/site-direction.md), and
[D029](decision.md#d029---static-evidence-site-with-original-reusable-system-art)
record the direction. Six pages and a 404 are implemented in [frontend](frontend/).
The build copies allowlisted sanitized recordings, factual `llms.txt`, font
licenses, source documents, and a six-page canonical sitemap. The original SVG
system supports the homepage breakdown and Engine's manual Flow/recorded Replay.
Results derives charts/tables from retained raw experiments, including regressions.

**Verification checkpoint (2026-10-18):** `./scripts/frontend.ps1 build` passes
with project-local Node 24.22.0/Vite 8.3.4. Four [data/artifact checks](frontend/tests/evidence.test.mjs)
pass: source-event/attempt identity and timestamps, provenance rejection,
raw-to-chart measurement reproduction, canonical entries, and private-token/design-
contract absence from public files. Nine [browser checks](frontend/tests/browser/site.spec.js)
pass in 29.3 seconds; [actual report](artifacts/verification/frontend-browser.json).
They cover six direct production-base routes at 1440/390/320 px, no overflow,
asset/JavaScript errors, or privileged requests; tab keys/focus/history; scenario
switching, interventions, actual outcomes; hidden/reduced-motion replay; exact
confirmation values and regression; mobile menu/FAQ/copy/preference; evidence
retry; instrumented Canvas suspension when paused/offscreen/hidden; and axe
WCAG A/AA checks across all six pages and both Engine views. These automated
checks supplement static diagram and screenshot review, not a
claim of universal accessibility certification. Desktop/mobile captures are in
`.impeccable/review/`, with font/overflow metadata in `capture.json`. The one
Impeccable mechanical scan returned no findings. Design finish review and the
shipped design-system record remain in progress, so P8.5 is still open.

**Phase 8 closeout (2026-10-18):** after the finish review's two material fixes,
all **10 browser checks pass in 31.9s**. The added check directly retrieves
`llms.txt`, parses the sitemap as XML against its six expected canonical URLs,
and verifies the 404 recovery link. The updated mobile check exercises the
diagram's shared manual layer selector. Test conditions now use readable 14px
text at every viewport. The reviewer scored both requested fixes **resolved**,
with disposition **ship** at the fix-list scope; [review record](.impeccable/review/finish-review.md).
All fourteen desktop/mobile captures were refreshed. The new-world record in
[design.md](design.md) and [.impeccable/design.json](.impeccable/design.json) derives
from the finished code. The earlier design discussion is preserved intact in
[discussion-history.md](artifacts/design/discussion-history.md). Missing separate
QUALITY BAR cards and standalone seed-roll archival evidence are disclosed;
no whole-surface certification is claimed. [Local verification](artifacts/verification/frontend-local.json)
records runtime, build, tests, review scope, and 27 frontend source hashes.
**P8.1-P8.5 are complete locally.** Public hosting and hosted frontend CI remain
Phase 9 verification, not claimed by these local checks.

### Phase 8 revision - user feedback of 2026-10-19

The original baseline is locally verified but its structure was rejected by the
user. Their supplied lifecycle screenshot and seven concrete criticisms take
priority over the old fix-scoped review. Preserve the original task IDs above;
the revision is tracked separately here.

- [x] P8.R1 Revisit Griffin through Playwright CLI, inspect baseline using Taste,
  and record the argument, section structure, and direction before implementation.
  See [revision record](artifacts/design/revision-2026-10-19.md), research captures,
  and the persisted surface brief. Palette and typography assets are retained.
- [x] P8.R2 Replace the repeated hero graphic with a readable handoff interaction;
  give the original pixel field sufficient contrast and retain pause/static modes.
- [x] P8.R3 Keep one compact exploded architecture moment and replace the rejected
  lifecycle/recovery duplication with one continuous actual job/attempt history.
- [x] P8.R4 Use distinct Flow/Replay visuals and reduce repeated Engine invitations;
  normalize decorative action icons across all six pages.
- [x] P8.R5 Animate FAQ opening/closing with accessible buttons/regions, reversal,
  one open answer, and a true zero-duration reduced-motion fallback.
- [x] P8.R6 Verify routes, contrast, mobile/tablet/desktop, source data, interaction,
  animation/pixel behavior, production build, and a fresh full design review.
- [x] P8.R7 Update the shipped design system and behavior/setup/decision records
  from the reviewed revision. Preserve prior evidence as historical checkpoints.

**Revision verification (2026-10-19):** production build and four data/artifact
checks pass. All **14 browser checks pass in 34.2s**; [report](artifacts/verification/frontend-browser-revision.json).
The added regressions directly verify one exploded view, at most two Home main
Engine links, distinct Flow/Replay visuals, unchanged illustrative job identity
with one owner, FAQ reversal/single-open/zero reduced-motion duration, and visible
glyph pixels on graphite. Existing route, evidence, keyboard, axe A/AA, utility,
Canvas suspension, mobile, hidden-playback and error recovery checks still pass.
All six routes were checked at 1440/390/320px. Fresh desktop/mobile screenshots
and a 768px Taste inspection are captured.

**Review correction (2026-10-19):** the fresh full review identified one material
issue: later CSS erased selected states in scenario/effect/measurement filters.
The correction adds a persistent selected fill distinct from hover/focus. The
new regression checks all four filter groups at desktop/mobile using pointer and
keyboard selection. All **15 browser checks pass in 45.8s**, plus the four data
checks and production build. All desktop/mobile captures were refreshed; changed
filter-state captures were added. The [reviewer](.impeccable/review/revision-finish-review.md)
scored the one requested fix **resolved**, disposition **ship** at fix scope.
The shipped system is recorded in [design.md](design.md) and its schema-version-2
sidecar. The 18 October system is preserved in `artifacts/design/baseline-2026-10-18/`;
discussion history remains intact. README, working guide, D030 and project memory
describe the revision. [Revision verification](artifacts/verification/frontend-revision.json)
records source/design hashes, scope and limits; [tool verification](artifacts/verification/agent-tooling-2026-10-19.json)
records the separately requested Trail Code/Anatomy installations. **P8.R1-R7 are
complete locally.** Deployment remains deferred.

### Phase 8 design round - user approval of 2026-10-21

The user rejected the 19 October composition and technical copy. Preserve all
earlier task IDs and verification as history, not acceptance of the new design.
The approved workflow is mockups first on Impeccable's native decision page,
then the selected desktop build, then desktop review before responsive work.

- [x] P8.D1 Record the Cierto page/interaction study and the revised newcomer-first
  brief, distinguishing observed behavior from its demo's unverified startup.
  Verification: saved page/route inventory, eight public-page and seven Docs
  reports, utility responses, before/mid/after FAQ measurements, hover/SDK/menu/
  Docs observations, and selected desktop captures under
  `artifacts/design/research/cierto-2026-10-21/`. Source session:
  `cierto-study-v2`; native direction roll: `0385e4c2`, API pool `c3b204a1eed6`.
- [x] P8.D2 Present three polished Home/Engine visual directions on the actual
  Impeccable decision page, with selection, feedback, and same-page re-roll.
  Notify the user when the mockups are ready. No frontend build before selection.
  Verification: six 1536x1024 builtin mockups inspected; all six contain embedded
  exact prompts (`embed-prompt --scan`: 6 rasters, 0 missing). Native decision
  page at `http://127.0.0.1:55091/` shows three Home options; matching Engine PNGs
  load in adjacent Chrome tabs through the local static preview. Readiness
  capture/report are in `artifacts/design/research/cierto-2026-10-21/`;
  [mockup manifest](artifacts/design/relevo-mockups-2026-10-21.json) records paths,
  dimensions, hashes, source prompts, and explicit unapproved status. User notified.
  This checks presentation only; no website behavior or responsiveness is verified.
- [x] P8.D3 Record the selected direction and approved mockups; build desktop
  Home/Engine section by section with one scroll-driven Anatomy exploded view,
  edge-to-edge pixels, simple copy, short navigation, and fewer CTAs.
  Revised sequence authorized in chat: whole-site clickable desktop demo first;
  final website after demo feedback. The prior main source is archived; the
  isolated demo remains available as a historical comparison.
  - [x] P8.D3a Record regional hybrid approval and the isolated demo contract in
    `artifacts/design/desktop-demo-direction.md`: Museum colours, Exhibition
    type/hero, Assembly model content/composition, Museum Engine layout.
  - [x] P8.D3b Build the separate six-page clickable desktop demo with shared
    navigation/footer, actual evidence, model scroll and representative states.
    Verification: isolated bundle builds; all nine dedicated desktop checks pass
    (77.6 s, widths 1440/1920 only), plus four existing evidence/artifact checks.
    Zero axe A/AA violations across six routes and both Engine views. Actual
    source comparison confirms all 23 baseline `frontend/src` files unchanged.
    See `artifacts/verification/desktop-demo.json` and linked browser report.
  - [x] P8.D3c Verify/review the desktop demo, open it, and stop for user feedback.
    User accepted the structure and requested the D033 production corrections.
    This is user review and recorded checks; the interrupted prototype reviewer
    did not give a final ship verdict.
  - [x] P8.D3d Apply demo feedback and complete the approved main-site Home/Engine.
- [x] P8.D4 Verify desktop functionality and a fresh full desktop design review;
  show the working result and stop before tablet/phone changes or responsive tests.
- [x] P8.D5 After the desktop review, apply the chosen direction to the remaining
  pages and update the shipped design record from the actual implementation.
  Latest explicit approval includes all six desktop pages in this production pass.
- [ ] P8.D6 In the later responsive stage, adapt and verify tablet/phone layouts;
  complete the full frontend gate only with actual evidence.
- [x] P8.D7 Apply the subsequent desktop feedback: consistent branding/type,
  larger hero with the subsequently authorized illustrative handoff, compact
  immersive model scroll, smooth illustration hover, retained non-fluid pixels,
  explicit Application/Recovery Flow states and Docs scrollspy. Preserve Replay
  and verify/review desktop changes before the responsive stage. Evidence below.
- [x] P8.D8 Replace the rejected worker-node hero animation with a minimal
  functional example over active random pixels inside the hero background only;
  remove the bottom strip and reveal Home content on viewport entry. Verify desktop behavior,
  reduced motion and fresh design review; retain the approved system/model.

- [ ] P8.D9 Keep navigation visible with slight scroll transparency; remove the
  Home hero report animation while retaining its pixels. Verify desktop anchor
  access, Docs index and the model below navigation; refresh the current records.

**Earlier D033 production desktop checkpoint (2026-10-21):** P8.D1-D5 and P8.D3a-d are
complete locally. The user accepted the demo structure and authorized D033's
production corrections across all six pages. Build and four data/artifact checks
pass. All **11 dedicated desktop browser checks pass** (one worker, no retries,
1440/1920px; final clean serial run about 1.3 minutes). They cover routes/base URLs,
four model depths and reverse/fast scroll, Canvas movement/coverage/suspension,
hover/focus/press/selected states, both Flow paths, actual Replay, Results,
FAQ reversal, keyboard access, reduced motion and recoverable errors. Seven axe
scans across six pages and both Engine views report zero violations.

The fresh full [desktop design review](.impeccable/review/production-desktop-finish-review.md)
requested a 40px closing Home heading and replacement of inherited design
records. The reviewer subsequently scored **both fixes resolved**, disposition
**ship at fix scope**. The corrected section was computed/captured at 1440/1920;
[fix evidence](artifacts/verification/production-desktop-review-fix.json).
The shipped documenter derived design.md and .impeccable/design.json from
the actual implementation. The one detector warning concerns user-pinned type;
Taste's generic photo/video/larger-type/palette recommendations do not override
the explicit selected hybrid. Their dispositions are retained in the review.

[Verification manifest](artifacts/verification/production-desktop.json) records
source/design/capture hashes, reports, resource limits and deferred work.
The prior main is archived under
artifacts/design/baseline-2026-10-21-pre-integration; the earlier demo remains
in frontend/prototype. Backend APIs and retained evidence are unchanged.
Preview: http://127.0.0.1:4173/Relevo/ . Stop for user desktop feedback.
**P8.D6 remains open: no tablet/phone adaptation or responsive verification was
performed for this redesign. The complete frontend gate and deployment remain open.**


**Earlier D034 desktop refinement checkpoint (2026-10-21):** P8.D7 is complete locally.
The production build and four data/artifact checks pass. All **14 dedicated
desktop checks pass** (one worker, no retries; 1440/1920px, about 1.5 minutes).
They include four model depths/containment/reversal, fixed pixel positions with
live opacity and rendering suspension, bounded hero playback/replay/hidden-tab
and reduced-motion states, branding/type/hover, Application and Recovery Flow
highlights, actual Replay, Results, FAQ, keyboard access and recoverable errors.
Seven automated axe scans report zero desktop A/AA violations. After that full
run, cold Docs fragment alignment was corrected; its enhanced entry/reload and
bidirectional reading-position check passed again. No other UI changed.

The fresh full [refinement review](.impeccable/review/desktop-refinement-finish-review.md)
found no material UI defect and requested only current design records. The
documenter refreshed design.md and its schema-v2 sidecar from final source; the
reviewer scored that persistence fix resolved, **ship at fix scope**. The detector
ran once before the final hero addition; the fresh reviewer manually inspected
that addition. No second detector or new option round was run.

[Refinement manifest](artifacts/verification/desktop-refinement.json) links reports,
source/capture hashes, the final targeted Docs confirmation and limits. Earlier
Chrome network suspension is retained as intermediate environment evidence; the
clean serial run passed. Backend APIs, recordings and measurement formats remain
unchanged. The desktop preview is ready for user feedback. **P8.D6 remains open;
no tablet/phone adaptation, responsive testing or public deployment is claimed.**

**Home motion verification (2026-10-22):** P8.D8 is complete locally. The old
worker-node hero is replaced with an explicitly illustrative report example;
one random pixel field fills the hero background, with no bottom strip. Home
groups reveal on entry, remain visible on return and appear immediately for
keyboard focus/reduced motion. The original four-depth model is preserved.

All **15 distinct desktop checks are verified** at 1440/1920px across the main
run (12 passes) and a three-check confirmation. The latter covers all six routes,
hero pixel pattern/coverage/suspension and seven settled-state axe scans with
zero violations. The main run's route fixture had a Chrome launch failure; its
pixel edge test assumed the old strip's density, and its scan began before the
lazy Home page mounted. Tests now wait for actual content and sample the hero's
intentionally sparse left region. The initial pass also caught and fixed footer
mounting before page load; it is verified to wait and enter on scroll. Build
and four data/artifact checks pass. No failed result was silently overwritten.

Fresh [Home review](.impeccable/review/home-motion-finish-review.md) and the
source-derived design record are complete. The review found only stale product
context; its refresh was scored resolved, ship at fix scope. The detector ran
once and returned no findings. [Evidence](artifacts/verification/desktop-home-motion.json) records
the reports, combined check coverage, source/capture hashes and limits. Backend
APIs, actual Replay and benchmark formats are unchanged. Stop for user desktop
feedback; P8.D6 responsiveness and Phase 9 publication remain open.

## Phase 9 - Package and deploy within INR 0

- [ ] P9.1 Finish one-command local Compose startup with migration ordering, readiness, persistent storage, worker/scheduler startup, and optional tooling profiles. Document stop/restart, test execution, and backup/restore without making data deletion part of normal startup.
- [ ] P9.2 Publish concise actual setup/troubleshooting instructions, the architecture/working guide, benchmarks/raw results, and a short recorded failure-recovery demonstration. Replace planned paths/commands only with verified ones.
- [ ] P9.3 Recheck GitHub Pages eligibility/current terms and configure the Vite base path for the actual repository before deploying the static site. Its free `github.io` address is the proposed public URL; a paid domain is outside scope.
- [ ] P9.4 Assess a live engine only if an Oracle Cloud Always Free instance is actually available and the full configuration fits ongoing free quotas. Recheck current terms, capacity, architecture compatibility, storage, and network exposure before provisioning. If unavailable, ship local Compose plus recorded evidence; do not substitute paid hosting or trial credits.
- [ ] P9.5 Verify a clean-clone build, CI, local demonstration, frontend links/assets, and secret-free artifacts. Check that the deployed `llms.txt` and `sitemap.xml` are directly retrievable and that their URLs respect the actual origin/base path and resolve to published pages. For any live engine, verify token-protected controls, private database/metrics access, persistence, backup/restore, and restart behavior. Record the actual hosting outcome and limitations.

**Completion check:** another developer can run and test Relevo, reproduce its evidence, and understand its guarantees. The public explanation does not depend on a paid or continuously available live service.

**Evidence:** pending implementation.

## Next session

**Current priority (2026-10-22):** review the completed six-page desktop website
with the user at http://127.0.0.1:4173/Relevo/ . D035 / P8.D8 Home motion refinement,
checks, fresh review and design records are complete locally. Stop
here before tablet/phone adaptation or responsive verification (P8.D6).

Backend Phases 1-7 remain complete at their recorded checkpoint. Earlier Phase 8
completion claims refer to historical designs; the current full frontend gate
is open until the separate responsive stage is verified. Hosted frontend CI,
clean-clone/operational verification and free-only deployment remain Phase 9 work.
No public release, paid service or additional PC application is claimed.

## Deployment readiness release — user authorization 31 October 2026

Supersedes desktop-only scope and earlier GitHub Pages/Oracle assumptions.
- [ ] P9.R1 Preserve release branch, inventory/clean sources, archives and secrets.
- [ ] P9.R2 Root-path Vercel build, canonical/sitemap/LLM utilities and headers.
- [ ] P9.R3 Complete six-page responsive layout and functional/a11y verification.
- [ ] P9.R4 Fresh backend lint/unit/PostgreSQL/network/crash verification.
- [ ] P9.R5 Isolated database backup/restore proof and deployment runbook.
- [ ] P9.R6 Exact committed checkout, hosted CI and release PR; no merge/deploy.
- [ ] P9.R7 Final evidence-based verdict; cloud-only checks explicitly deferred.

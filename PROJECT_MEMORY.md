# Relevo project memory

Recorded: 2026-10-16 (Asia/Calcutta).

## Accepted direction

- Build boundary confirmed 2026-10-17: continue backend work through Phase 7.
  Have a conversation with the user before beginning frontend implementation,
  even after the backend readiness gate passes.

- Name: **Relevo**, Spanish for replacement or a relay handoff; the name represents
  workers taking over interrupted jobs.
- Description: **A durable task execution engine.**
- Frontend introduction: "Explore how jobs are claimed, retried, and recovered
  when workers fail."
- Purpose: demonstrate core backend and distributed-execution understanding for
  SDE/backend job applications: concurrency, transactions, coordination, delivery
  semantics, failure recovery, and performance.
- External user adoption is not an acceptance criterion for this project. This
  supersedes the earlier consumer-project discussion and BatchRadar proposal.
- Target effort: 6-8 weeks at 10-15 hours per week.
- Deployment budget: **INR 0, free-only**. This supersedes the earlier INR 1,000
  monthly budget and AWS Lightsail suggestion.
- At memory creation, this repository had no implementation. The items below are
  design decisions and planned work, not completed or verified capabilities.

## Technology direction

- Backend: Python 3.13, FastAPI, Pydantic, PostgreSQL 18, SQLAlchemy with Psycopg,
  and Alembic migrations.
- Worker runtime: Python multiprocessing; HTTPX for coordinator communication.
- Frontend: React + **JavaScript**, Vite, and CSS. The user explicitly chose
  JavaScript instead of TypeScript.
- Setup preference (2026-10-16): handle required project dependency downloads and
  installation; tell the user if a separate PC application or system setup is
  needed. Check existing tools before requesting installs and identify any steps
  that require their action.
- Tooling: Docker Compose, pytest, Toxiproxy, OpenTelemetry,
  Prometheus/Grafana, and GitHub Actions.
- Implement leases, scheduling, retries, and recovery in the project itself.
  Celery, Kafka, and Kubernetes are not part of v1.
- Use explicit SQL for critical claiming and ownership operations.

## Engine design and guarantees

- Components: coordinator API, independent recovery scheduler, independently
  restartable workers, and PostgreSQL as the single durable authority.
- Core tables: `jobs`, `attempts`, and `job_events`. Add a separate demonstration
  business-effect ledger for idempotent-effect tests.
- State machine: pending -> running -> succeeded or failed. Retryable attempts
  return the job to pending with a future availability time. Delayed jobs stay
  pending until eligible. Terminal jobs cannot be reset in v1.
- Acknowledge submission only after its database transaction commits. Preserve
  normal PostgreSQL durability settings.
- Require submission idempotency keys. Identical normalized requests return the
  existing job; a different request with the same key returns a conflict.
- Atomically claim available jobs using short transactions and
  `FOR UPDATE SKIP LOCKED`; create the attempt and ownership in the same transaction.
- Each attempt has a worker identity, incrementing fencing token, and expiring
  lease. A job has at most one valid lease at a time.
- Only the current unexpired owner may renew or report a new outcome. Reject stale
  state updates. An identical already-committed report may be acknowledged again
  without another transition; conflicting reports must be rejected.
- Use database time for eligibility and lease decisions. Do not hold database
  locks while executing task code.
- Commit state-transition history with the state changes it describes.
- Retry expired or failed attempts with bounded exponential backoff and jitter.
- Every acknowledged job must remain accounted for in a valid state.
- Recovery can execute a task more than once. Fencing protects executor state;
  external business effects need their own idempotency protection. Do not claim
  exactly-once external effects or resumption from the interrupted instruction.

## V1 bounds and interfaces

- Defaults: 15-second leases, 5-second heartbeats, 2-second recovery scans,
  3 total attempts, 60-second task execution limit, and 64 KB payload/result limits.
  Timing defaults must be configurable for tests.
- Each worker claims one job and runs a registered handler in a child process.
  Stop the child on rejected ownership, unconfirmed renewal, or execution timeout.
- Initial handlers: payload hashing, timed work, and configured transient failures.
- Support immediate and delayed tasks through `run_at`.
- Provide job submission, status lookup, attempt history, worker claim/heartbeat/
  complete/fail operations, health/readiness endpoints, and metrics.
- Provide a small Python client and CLI for demonstrations without the frontend.
- Trusted-cluster model with an environment-provided shared API token.
- Exclude remotely uploaded executable code, workflow graphs, recurring cron
  schedules, multi-tenancy, and a graphical administration dashboard from v1.

## Agreed HTTP endpoints

Preserve these exact HTTP methods and paths when implementing the API:

```text
POST /jobs
GET  /jobs/{id}
GET  /jobs/{id}/attempts

POST /internal/claim
POST /internal/attempts/{id}/heartbeat
POST /internal/attempts/{id}/complete
POST /internal/attempts/{id}/fail

GET  /health/live
GET  /health/ready
GET  /metrics
```

In job routes, `{id}` identifies a job; in internal attempt routes, `{id}`
identifies an execution attempt. Initial request/response contracts now exist in
`backend/src/relevo/api/schemas.py`. All ten endpoints are now implemented,
including leased ownership and fenced worker reports. A supervised worker now
executes registered handlers and an independent scheduler recovers expired
attempts. See the dated implementation progress below for evidence and limits.

## Tests and evidence

- Use real PostgreSQL integration tests for concurrency and transactional behavior.
  Synchronize around known execution points instead of arbitrary sleeps.
- Required scenarios: concurrent duplicate submission; competing workers; death
  after claiming; interrupted heartbeats; stale completion after reassignment;
  lost submission/completion responses; database, coordinator, and scheduler
  restarts; delayed jobs; exhausted retry budgets; poison-job isolation.
- Demonstrate a business effect committed before completion reporting fails:
  recovery repeats execution. Then show handler-level business idempotency
  preventing a duplicate effect.
- Use Toxiproxy for controlled connection failures and latency.
- Logs identify job, attempt, worker, and transition. Measure queue delay,
  execution duration, retries, expired leases, stale reports, and database latency.
- Benchmark identical workloads with 1, 3, and 5 workers. Include short and longer
  tasks, repeated runs, hardware/configuration, throughput, queue delay, API
  latency, CPU, memory, and database contention. Explain measured bottlenecks.

## Frontend and free deployment

- The frontend is an explanatory portfolio experience: plain-language use cases,
  an architecture explorer, job lifecycle, failure/recovery demonstration, attempt
  timeline, guarantees and limitations, benchmark methodology/results, quickstart,
  and repository link.
- Use clearly labeled replay of actual recorded test events for the public
  interactive demonstration. Link the corresponding test script or recording.
  Do not present synthetic events as measured execution.
- Public replay must not expose privileged worker controls or shared API tokens.
- Require responsive layouts, keyboard-accessible controls, reduced-motion
  support, and diagrams understandable without animation.
- Proposed frontend host: GitHub Pages with its free `github.io` address.
- Proposed live-engine option: Oracle Cloud Always Free VM, only if an eligible
  instance is available and remains within free quotas. At planning time Oracle
  documented 2 OCPUs/12 GB for Always Free ARM tenancies, with possible idle-instance
  reclamation. Recheck current quotas and availability before provisioning.
- Keep the explanatory frontend and recorded demonstrations independent of live
  engine availability. The complete engine must also run locally through Compose.
- A domain purchase, paid VM, paid database, or paid fallback is not authorized.
- Frontend visual design direction and actual hosting availability are unresolved.

## Delivery order

1. Define guarantees, state machine, architecture, and limitations.
2. Implement durable submission, migrations, atomic claims, and concurrent tests.
3. Add worker supervision, leases, heartbeats, scheduling, retries, and recovery.
4. Prove crash/network/race scenarios and idempotent business effects.
5. Add telemetry, benchmark, and improve one measured bottleneck.
6. Build the explanatory frontend from verified engine behavior and evidence.
7. Deliver one-command Compose startup, CI, concise documentation, benchmark
   scripts/report, and a short recorded failure-recovery demonstration.

Do not mark a capability complete until its corresponding implementation and
verification exist. Record later changes and completed milestones here.

## Documentation baseline - 2026-10-16

- Added `implementation-plan.md` as the ordered build checklist, progress tracker,
  phase gates, and home for implementation/verification evidence.
- Added `decision.md` as the rationale log for consequential technical choices,
  including the accepted direction above and explicitly identified implementation
  refinements. Accepted design does not mean implemented behavior.
- Added `working.md` as the plain-language explanation and `README.md` as the
  entry point and future home of verified setup commands.
- Updated `AGENTS.md` to direct future sessions to these files and preserve the
  backend readiness gate before frontend implementation.
- Documentation baseline complete. No application code, tests, benchmark results,
  frontend, or deployment exists yet. Next: implementation plan Phase 1, starting
  with P1.1 (backend foundation and contracts).

## Backend milestone - 2026-10-16

- Initialized the local Git repository (no remote, commits, or hosted CI run yet).
- Implemented the Python package, validated settings, shared-token authentication,
  HTTP contracts for all ten routes, structured/redacted errors, liveness,
  database/schema/durability readiness, and protected baseline metrics.
- Added `backend/uv.lock`, uv 0.13.1 tooling, digest-pinned container images,
  Alembic migration `0001`, and `jobs`/`attempts`/`job_events` constraints/indexes.
- Implemented durable submission, canonical request fingerprints, transactional
  idempotency/conflicts, status lookup, and ordered attempt-history reads.
- Payload limit: 65,536 canonical UTF-8 JSON bytes; raw POST-body limit: 1 MiB.
  Scheduling timestamps normalize to UTC; omitted/null `run_at` means immediate.
- Compose runs the API, migration step, and persistent PostgreSQL 18.6; a separate
  ephemeral PostgreSQL test service protects development data. Local random
  credentials live in ignored `.env`; no extra PC application was required.
- Verified 47 tests on Windows/Python 3.13.9 and Linux/Python 3.13.16 against real
  PostgreSQL, including concurrent submissions, rollback/commit boundaries, lost
  response replay, byte limits, authentication, and migration round-trip/drift.
- Verified container readiness and live API submission, replay, conflict, lookup,
  history, and metrics. Added a GitHub Actions workflow; hosted execution is still
  unverified until a remote is configured.
- Current jobs remain pending. No atomic claiming, heartbeat/completion/failure
  logic, worker runtime, scheduler, business-effect demo, benchmarks, public
  frontend, or cloud deployment is implemented yet.
- Next: Phase 3, atomic ownership and fenced reports. Backend gate remains open.

## Ownership milestone - 2026-10-16

- Completed Phase 3: explicit `FOR UPDATE SKIP LOCKED` claims, atomic
  job/attempt/event assignment, job-first locking, database-time ownership checks,
  heartbeat renewal, and fenced completion/failure. Internal routes now function
  instead of returning `501` placeholders.
- Fresh expiry checks occur after locks and in the final guarded ownership write.
  Heartbeat renewal never shortens a lease and adds no state-transition event.
- Migration `0002` adds a partial unique index preventing two running attempts
  for one job. Migration `0001` is preserved.
- Persisted report fingerprints/responses acknowledge identical committed
  outcomes even after expiry or reassignment; changed reports/wrong identities
  conflict. The acknowledgment is historical; query the job for current state.
- Implemented delayed eligibility and bounded reported-failure retry policy as
  Phase 3 dependencies (P5.1/P5.2): equal jitter between half/all of an exponential
  ceiling, default 1-second base and 30-second cap, with three total attempts.
- Added finite date/time configuration bounds, signed-64-bit fencing validation,
  result byte limits, and JSON-safe errors. Preserve old acknowledgments when
  only configurable payload/result admission limits are lowered; reject new
  over-limit work.
- Verified 103 tests on Windows/Python 3.13.9 and Linux/Python 3.13.16 against
  PostgreSQL 18.6; nine synchronized concurrency/lock-expiry checks passed five
  consecutive rounds. Tests include observable database lock contention, stale
  ownership at lock/write boundaries, claim/report races, exact/conflicting
  replays, lost report responses, rollback, and total-budget exhaustion.
- Rebuilt and started the installed runtime with schema `0002`; readiness is
  healthy. Coordination tests use controlled reports, not actual handler runs.
- Remaining: supervised worker/handlers (Phase 4), independent expiry recovery
  scheduler (Phase 5), full crash/network/business-effect evidence, telemetry/
  benchmarks, frontend, and free deployment. Expired attempts are fenced but are
  not automatically reassigned yet. Hosted CI still awaits a remote.
- Next: P4.1. Keep updating implementation-plan.md as verified steps complete.

## Worker implementation progress - 2026-10-16

- Phase 4 is in progress. Added HTTPX async coordinator calls with total request
  deadlines/bounded responses, a spawn-based supervisor, registered hash/timed/
  transient-failure handlers, bounded atomic-file result IPC, exact report
  delivery retries, shutdown handling, and a parent-liveness watchdog.
- Claims now include `lease_seconds` and `max_result_bytes`; renewals include
  `lease_seconds`. Workers use conservative request-start monotonic deadlines
  instead of comparing database expiry to local wall time. Coordinator and worker
  must be rebuilt together for this initial worker contract.
- Worker settings need only API URL/token; Compose adds an init-enabled worker
  without database credentials. Child handler entry removes Relevo credentials
  inherited from the environment. This is not a hostile-code sandbox.
- Verified lint/format and 50 synchronous component/configuration checks, including an actual Windows
  spawn, canonical hashing, input/output limits, pre/post execution deadlines,
  and credential removal. The current tree collects 137 tests. Only P4.4 is
  checked complete; supervisor/integration/restart verification remains pending.
- Compose syntax (`docker compose config --quiet`) and worker CLI help also pass;
  these do not establish runtime deployment behavior.
- Async checks stall in Windows `socket._fallback_socketpair` while asyncio
  initializes its self pipe under the agent sandbox. Stalled checks were stopped.
  Automatic approval review also hit its usage limit; no Docker cleanup, rebuild,
  or new container tests were executed after that review failure. The previous
  103-test full result applies to Phase 3, not this new revision.
- Asked the user to run `docker compose --profile test run --build --rm tests`
  and provide the result. Do not bypass the approval restriction. Continue with
  permitted workspace work and resume full verification when possible.
- Next: validate Phase 4, then implement the Phase 5 recovery scheduler. Keep the
  frontend gate closed and avoid claiming worker/recovery guarantees prematurely.

## Worker and recovery milestones - 2026-10-16

- The earlier automatic approval service usage block cleared. Approved Docker
  and native Windows execution resumed; no manual user test run is now needed.
- Completed Phase 4's supervised worker and Phase 5's independent recovery
  scheduler. The full suite passes **152 tests on Windows/Python 3.13.9 and
  Linux/Python 3.13.16 against PostgreSQL 18.6**. Lint/format checks pass.
- The scheduler uses bounded skip-locked batches (default 100, configurable
  1-1,000), job-before-attempt locks, fresh database-time revalidation, and a final
  guarded expiry write. Expiry, retry/final failure, and history commit together.
  It stores no cursor in memory and runs independently of API startup.
- Verified concurrent scanners, bounded batches, locked-row skipping, post-lock
  revalidation, rollback at event/commit boundaries, exhausted expiry budgets,
  healthy-job isolation, stale heartbeat/completion races, new scheduler processes,
  and actual handler completion after a committed-but-unreceived claim.
  Six recovery concurrency/rollback cases also passed five consecutive rounds
  (30 executions), in addition to the full Windows/Linux suite results.
- Rebuilt Compose with API, worker, scheduler, and migration ordering; startup
  passes. Live worker hashing/transient-failure checks pass before/after a
  worker-only restart with a new process identity.
- Added reusable `scripts/smoke_worker.py` and `scripts/smoke_recovery.py`.
  The latter passed a real worker-container SIGKILL during timed execution with
  the scheduler stopped: the job remained recorded, scheduler restart scheduled
  recovery, and a replacement attempt succeeded with a higher token/new worker.
  The original attempt's late completion returned `409`.
- `decision.md` records D020's verified worker boundary and D021's bounded
  transactional recovery choices. Plan tasks P4.1-P4.6 and P5.1-P5.5 are complete.
- This is local process/container correctness evidence, not the entire Phase 6
  network/storage/business-effect failure matrix. Isolated orphan cleanup is
  best effort, and no exactly-once external-effect claim is made. Hosted CI
  remains unverified without a remote. No extra PC application was needed.
- Next: Phase 6 fault evidence, business-effect idempotency, Python client/CLI,
  and traceable recordings; then telemetry/benchmarks and the backend gate. Keep
  frontend implementation behind that gate.

## Phase 6 milestone and Phase 7 scope - 2026-10-17

- Phase 6 is complete locally: the public async Python client/CLI, isolated
  Toxiproxy TCP faults, independent demo business-effect transactions/migration
  `0003`, actual API/database/worker/scheduler crash/restart evidence, sanitized
  recordings, and accounting checks after every PostgreSQL test are implemented.
- Full Phase 6 results: 185 tests passed on Windows and Linux. On 2026-10-17,
  81 integration tests passed three additional rounds (243 executions).
  A fresh worker crash recording passed after the earlier approval limit cleared.
- Recordings under `artifacts/replays` include real state/history and source/config
  metadata; effect tests label direct deadline injection and instrumented handler
  execution. Runtime child credentials are unchanged. No exactly-once claim.
- User requested completing backend work through Phase 7, then a conversation
  before frontend work. Phase 7 implementation has begun; do not start Phase 8.
- User created/provided https://github.com/Tirthpanchori/Relevo. It is connected
  as `origin` and initially empty. Source review, local checkpoint/push, and hosted
  Actions execution remain; no successful hosted CI result is claimed yet.
- OpenTelemetry SDK and OTLP HTTP exporter are being added for Phase 7. Keep
  durable event-derived totals separate from process-local metrics/traces. Next:
  finish observability checks, measure repeated 1/3/5-worker workloads, test one
  bounded optimization, and audit the backend gate with actual results.

- GitHub checkpoint `43ef7a8` is pushed to the user-provided repository. Hosted
  Actions run 39023521222 passed (including the full 195-test container suite).
  Local secret review passed; `.env` and monitoring credentials stay ignored.
  A corrected benchmark harness checkpoint `84e7d05` adds ANSI-safe Docker stats
  parsing and rejects missing resource samples. The discarded initial sampling
  pilot is preserved and excluded from performance comparisons.

## Phase 7 observability checkpoint - 2026-10-17

- P7.1-P7.3 verified: per-process protected metrics, redacted structured committed
  transition logs, explicit SQL/engine/HTTP traces, and worker/API propagation.
- Read-only database scrapes derive states, transition/retry totals, and persisted
  queue/attempt-duration histograms. Missing old timings are excluded; unavailable
  durable metrics are omitted with an explicit up=0 signal. Runtime telemetry can
  reset/drop observations. Retained-history scans are a documented scaling limit.
- Optional digest-pinned local Prometheus/Grafana/Jaeger starts and passes the
  actual scrape/dashboard/distributed-trace smoke. No native app install needed.
- Full current suites: 195 tests pass on Windows (49.33s) and Linux (32.08s), with
  TCP faults included. Invalid optional child timing cannot alter task outcomes.
- Added the isolated benchmark profile and fixed-workload harness/methodology.
  No performance result or promoted optimization exists yet; worker monitor
  interval remains 0.05 seconds. Next: committed baseline, repeated measurements,
  one measured improvement, hosted CI, clean-checkout audit, and Phase 7 gate.

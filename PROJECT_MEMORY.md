# Relevo project memory

Recorded: 2026-10-16; updated through 2026-10-31 (Asia/Calcutta).

Release progress (1 November): Docker is working. Locked Linux/PostgreSQL/TCP-fault suite passed 197 tests (84% coverage), lint and format passed (79 files), three process smoke checks and isolated restore proof passed. Frontend build, four artifact tests and all 23 browser tests passed, including 21 zero-violation axe scans. Design review agents hit usage limits: no independent release signoff claimed. CI/clean checkout/PR gates remain pending until recorded below. Earlier startup failure is historical.

## Current release authorization — 31 October 2026

The user approved full deployment readiness: responsive phone/tablet/desktop,
repository cleanup, fresh backend/frontend tests, backup/restore, deployment
instructions, and a pushed release PR with verified CI. This supersedes earlier
desktop-only stops. Frontend target Vercel at origin root. Assess Render compute
and Supabase PostgreSQL; private-token backend only, website recordings remain.
No cloud provisioning, merge or deployment. INR0 remains binding; report hosting
incompatibility rather than silently using paid workers or expiring trials.
Branch: release/deployment-readiness. P9.R1-R7 track current work, not completion.

## Accepted direction

- Latest refinement (22 October 2026): keep the navbar visible while scrolling,
  with a slightly translucent forest surface after scrolling. Remove the monthly
  report animation/card from Home hero; keep the left copy and active hero-only
  pixel background. Preserve lower report illustration, model, section entrances,
  evidence and desktop-only boundary. D036 / P8.D9 verification is pending.


- Latest Home correction (21 October, refined 22 October 2026): replace D034's worker-node hero
  animation with a minimal functional report example on the right, over an
  actively regenerating pixel background, while retaining the left headline.
  On 22 October the user removed the bottom pixel strip entirely: keep one
  actively regenerating field inside the hero background only. No liquid distortion or pointer displacement. Home
  content should reveal when scrolled into view, as in the supplied Cierto
  screenshot/reference. Keep approved colours, typography, section structure,
  four-level model, backend evidence and desktop-only boundary. Implementation
  and verification are complete locally under P8.D8 / D035: 15 distinct desktop
  checks verified across the main run (12 passes) and three-check confirmation;
  seven settled-state axe scans report zero violations. Build, four data/artifact
  checks and design-record refresh complete. Fresh review found only stale
  product context; the reviewer scored its refresh resolved at fix scope. Evidence:
  artifacts/verification/desktop-home-motion.json. D034 remains historical.
  Stop for desktop feedback before P8.D6 responsive work or publication.

- Further hero/model correction: the user finds the larger empty hero too sparse
  and explicitly authorizes a functional animation on its right (superseding the
  earlier no-hero-widget rule for a small illustrative handoff). Keep the pixel
  field itself; remove only liquid/displacement motion. Strengthen the model's
  immersion with camera framing, more continuous depth motion and a shorter pin.
  Preserve the other requested desktop refinements and the responsive stop.

- Latest desktop feedback (21 October 2026): retain the selected world and Replay;
  unify wordmark/tab branding and type roles, enlarge the hero's space rather
  than returning to oversized type, shorten/enlarge the model scroll with more
  immersive depth, smooth the report/ticket hover, add a lime wordmark sweep,
  remove fluid/pointer pixel response, make Application and Recovery explicit
  Flow highlights, and track the visible Docs section during ordinary scrolling.
  This is a desktop refinement, not a new design round or responsive stage.
  P8.D7 / D034 are implemented and verified locally at desktop scope: 14 browser
  checks passed, followed by the enhanced Docs check after the final fragment
  correction, plus four data/artifact checks. Seven axe scans report zero
  violations. Fresh full review found only stale records; their refresh was
  scored resolved, ship at fix scope. The desktop is ready for user review.
  Evidence: artifacts/verification/desktop-refinement.json. P8.D6 stays open.

- Earlier production instruction (21 October 2026; D033 checkpoint): the user reviewed the demo,
  likes its structure, and explicitly authorized the smaller-type / meaningful-
  depth / livelier-motion plan for ALL SIX production desktop pages. Integrate
  the demo, highlight “recover” in lime, reduce headline/body/control sizes, make
  pixels live, add coherent hover/press/focus and state transitions. The user
  selected FOUR SYSTEM LEVELS: Coordinator, Workers, Recovery, Saved record.
  Scroll must expose and explain each depth, rather than just lifting a lid.
  Preserve the Museum/Exhibition/Assembly regional choices and actual evidence.
  This supersedes the demo-only stop and preservation boundary below: archive
  the prior main source, retain the demo for comparison, then complete/review the
  desktop main site. No new option round. STILL STOP before tablet/phone work,
  responsive checks or publication. All six production desktop pages are built;
  eleven desktop checks and four data/artifact checks pass. The fresh reviewer
  scored both requested fixes resolved, ship at fix scope; the shipped documenter
  replaced the design records from code. Desktop is ready for user review, not
  completion of the full frontend. Contract:
  `artifacts/design/desktop-production-direction.md`.

- Earlier demo instruction (21 October 2026): user selected Museum colours,
  Exhibition typography and Home hero, Assembly model-section content/composition
  and model recoloured to Museum, and Museum Engine layout with Exhibition type.
  They then explicitly approved a separate clickable whole-site desktop demo
  BEFORE completing the final website. Cover Home, Engine, Results, Docs, About,
  Privacy, shared navigation/footer and missing-page recovery. Preserve the
  existing website. Use complete content, actual evidence, original Anatomy art
  and Motion; no new design-option tournament. Open the checked demo and STOP
  for feedback before the final build. No tablet/phone work or responsive tests.
  The regional authority and six-block contract are recorded in
  `artifacts/design/desktop-demo-direction.md`. Implementation is in progress;
  no demo checks or final replacement-site completion are claimed yet.

- Historical workflow (2026-10-21): the user explicitly authorized the revised
  frontend workflow: first three polished Home/Engine visual directions on the
  actual Impeccable decision page, with choose, feedback, and same-page re-roll.
  They selected mockups first, not three implemented websites. The primary reader
  is a curious newcomer; introduce familiar background-work examples before
  technical terms. Explore fresh palettes and typography. Build the selected
  desktop direction only after selection, show it for review, then stop before
  tablet/phone implementation or responsive verification. Use Graft for mapping,
  Playwright CLI for reference research, Anatomy for original scroll-driven
  exploded art, and Motion for purposeful interactions. Preserve React/JavaScript,
  backend contracts, actual evidence, and INR 0 recurring cost. This is an active
  design round; the subsequent hybrid selection above supersedes pending status.

- Mockup milestone (2026-10-21): P8.D1-D2 are complete. Six builtin 1536x1024
  mockups cover Exhibition, Museum, and Assembly, each with Home and Engine.
  Exact prompts are embedded (6 rasters, 0 missing) and retained in sidecars;
  `artifacts/design/relevo-mockups-2026-10-21.json` records paths/hashes. Native
  Impeccable decision URL `http://127.0.0.1:55091/`, key `002ab492`, payload
  `.impeccable/decisions/relevo-2026-10-21.options.json`. Visible Chrome/Playwright
  session `relevo-design-options` contains the page and matching Engine tabs.
  Static companion PNG preview is `http://127.0.0.1:61695/` (exec session 96532);
  decision launcher remains session 48636. User was notified that options are
  ready. The user subsequently selected a regional hybrid in chat, recorded
  above; do not wait for a single-card selection or start another round.
  Existing website remains unchanged; responsive work stays deferred.

- Historical priority (2026-10-20): pause further frontend changes for a clear
  project-understanding conversation. The user read working.md but found the
  terminology difficult. Explain the purpose and hypothetical real integrations
  through one concrete example before connecting jobs, attempts, workers,
  renewable leases, heartbeats, fencing tokens, eligibility, limits, and external
  effect safety. Distinguish processes from threads, retry from resumption, and
  current demo handlers from possible application integrations. An explanation
  being delivered is not evidence that the user has understood or approved more UI.

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
- Frontend visual direction is selected under D033, refined by D034, and the desktop production
  contract. Tablet/phone adaptation and actual hosting remain unresolved stages.

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

## Benchmark baseline milestone - 2026-10-18

- P7.4 baseline is complete: 18 retained cases, 540 measured jobs, two workloads,
  three repetitions, and 1/3/5 workers. Raw timings, request percentiles, container
  resource/lock samples, hardware/versions, source/image hashes, and unchanged
  PostgreSQL durability settings are in `benchmarks/raw/baseline-complete.json`.
- Excluded sampling/interruption/timeout runs are preserved and described in
  `benchmarks/README.md`. Fifteen valid cases were preserved across the timeout;
  three missing cases resumed only after runtime/configuration identity checks.
- Test the 5 ms child-monitor candidate against the 50 ms baseline before changing
  the default. P7.5/P7.6, clean-checkout verification, final log-redaction audit,
  and documentation closeout remain. Do not start the frontend.

- Candidate matrix also completed all 18 cases (540 measured jobs). The repeated
  comparison/CSV and explicit confounder notes are in `benchmarks/`. Do not claim
  its largest observed deltas are caused only by the polling interval; timed work
  with five workers showed a small regression and overlapping ranges.
- Fixed a proven Uvicorn exception-log redaction bypass. Full updated suite with
  5 ms configured passes 196 tests on Windows (36.72s) and Linux (28.83s).
  The default remains 50 ms until the separate same-image confirmation passes.

## Phase 7 measurement decision - 2026-10-18

- Confirmation completed all twelve cases (360 measured jobs); combined with the
  repeated matrices, 1,440 retained measured jobs have exact result/attempt/history
  validation. Reports/CSV/raw metadata are under `benchmarks/`.
- Keep the 50 ms monitor default. The configurable 5 ms option improved short jobs
  with one/three workers in confirmation but slowed timed work. D026 records the
  opt-in tradeoff; do not claim a blanket speedup or promote the candidate globally.
- Verified Windows' 180-second idle sleep and matching Modern Standby events for
  the rejected confirmation. Benchmark/checkout scripts now use temporary scoped
  awake requests; they restore prior thread state and do not edit the power plan.
- Uvicorn redaction regression fixed; full 196-test Windows/Linux checks pass.
  P7.5 is complete as measured optional tuning. Next: commit/push current evidence,
  clean-checkout startup/CLI/restart/full-suite verification, current hosted CI,
  and final P7.6 documentation/gate. No frontend work is authorized yet.

- Clean checkout `d3cc16b` passed startup with fresh credentials, terminal job/history
  replay after component restart, changed worker identity, and all 196 tests.
  Hosted CI 39066729992 also passed that checkpoint. Development data was preserved.
- Further audit fixed Uvicorn access logging being inadvertently re-enabled under
  `--no-access-log`; full updated results are 197 Windows (39.23s) and Linux (29.25s).
  Reverify the final source checkout/CI after this fix. Earlier benchmark revisions
  and their logging behavior are explicitly documented rather than relabeled.
- A crash-recording refresh succeeded on attempt three after an extra expiry.
  Preserve its diagnostic; D027 updates the harness to assert bounded valid
  expiry/history/fencing instead of an unsupported exact-two-attempt promise.

## Backend readiness gate complete - 2026-10-18

- Phases 1-7 and every backend gate are complete. Stop for the user-required
  frontend conversation; no React/Vite/frontend or cloud deployment has begun.
- Final code checkpoint `9af3ab8` passes 197 tests on Windows (39.23s), Linux
  (29.25s), a fresh checkout (197 tests, 27.80s), and hosted CI 39067364211.
- Fresh-checkout proof uses different credentials, rejects the original token,
  runs CLI before/after restart, preserves identical terminal job/history, and
  observes a new worker identity. Only new verification resources were removed;
  development storage/services were restored. Capture: `artifacts/verification`.
- Current crash/restart captures reference `9af3ab8`; effect captures reference
  verified `d3cc16b`. The extra-expiry diagnostic remains explicitly labeled.
  D027's stronger bounded-recovery smoke passes with actual SIGKILL and stale 409.
- Final monitoring smoke passes API/worker/scheduler targets, Grafana provisioning,
  and real distributed trace export. Compose 5 ms tuning completed a real CLI
  job, then restored the default 50 ms. Monitoring is running locally.
- Benchmark reports retain 1,440 measured jobs, raw timings/resources, regression
  and revision notes. Keep the conservative default; 5 ms is optional tuning, not
  a universal speedup. No exactly-once/uptime/storage-destruction claims.
- Remaining work: Phase 8 explanatory React/JavaScript frontend after discussion;
  Phase 9 free-only deployment/backup-restore/final packaging. No additional PC
  application or permanent power-setting change was required for Phase 7.

## Frontend design discussion - 2026-10-18

- The user has started the required frontend conversation. They want a minimal
  site with visual interest and supplied https://cierto-beta.vercel.app/ as a
  reference. It has been inspected in the browser; its typography, restrained
  palette, grid, and explanatory interactive graphics are reference material.
- The user requires a `design.md` companion to `implementation-plan.md` during
  frontend development: the design file will govern the agreed visual direction
  and interactions; the implementation plan will track tasks and verification.
- Visual direction is still being discussed. Recommendations are proposals,
  not accepted design decisions or implemented UI. No frontend code has begun.
- The user refined the references toward https://www.griffin.com/ for its
  layered hardware-like process breakdown and https://www.etched.com/ for its
  footer. Both were inspected in the browser. Griffin's isometric exploded
  system view and Etched's circuit-board/schematic line art are the relevant
  references. The user explicitly excludes borrowing either site's colours.
- The desired Relevo breakdown should explain its own distributed execution
  process. These references refine the visual discussion; no palette, final
  composition, animation implementation, or design contract is approved yet.
- The user clarified that all three references have distinct, concurrent roles:
  Cierto for website structure, thoughtful supporting pages, and light/dark
  blocks; Griffin for the design/breakdown inspiration; Etched for the footer.
  Do not treat Griffin as replacing Cierto's structural role.
- Added `design.md` as a draft information architecture: six proposed main pages
  (Home, How it works, Recovery Lab, Benchmarks, Docs, About), one Privacy page,
  and a not-found utility view. Navigation/footer/section proposals are recorded
  for this discussion, not accepted page scope or implemented UI. P8.1 remains open.
- The user rejected the crowded header and long names, and supplied Cierto's
  categorized footer screenshot. Required refinement: short labels, fewer header
  items, and Product/Evidence/Build/About footer groups. Preserve Etched-inspired
  footer artwork alongside this Cierto information hierarchy.
- Revised proposal in `design.md`: Engine, Replay, and Results replace How it
  works, Recovery Lab, and Benchmarks. Header: Engine, Proof (Replay/Results
  menu), Docs, plus GitHub action; logo returns Home. About/Privacy and detailed
  anchors sit in the grouped footer. These exact labels remain proposed; no
  page-count reduction or frontend implementation is implied.

## Accepted Engine and Replay merge - 2026-10-18

- The user accepted one Engine page with two tabs: Flow explains execution;
  Replay explores actual recorded failure scenarios. Show one active tab and
  one scenario at a time in a shared diagram workspace rather than stacking
  two full pages. Keep the homepage's exploded view a brief introduction.
- This supersedes the separate Replay-page and Proof-dropdown proposals above.
  Revised sitemap proposal: Home, Engine, Results, Docs, About, Privacy (six
  content pages plus the not-found utility view). Compact proposed header:
  Engine, Results, Docs, and GitHub; logo returns Home.
- Footer Replay and Watch replay actions open `/engine/#replay`; preserve the
  Product/Evidence/Build/About footer categories and all three reference roles.
- Recorded facts, explanatory diagrams, interventions, and timing compression
  remain distinct. Public replay stays token-free and works without a backend.
- `design.md`, decision D028, and the plan record the accepted merge. Palette,
  typography, detailed composition/motion, remaining content scope, and UI
  implementation/verification are still pending; P8.1 remains open.

## Footer discovery files - 2026-10-18

- The user requires an LLM text file and Sitemap in the footer. Record them in
  the About group as `llms.txt` and Sitemap (`sitemap.xml`). The user called the
  first `llm.txt`; the planned spelling follows the public llms.txt proposal.
- The LLM overview must summarize verified behavior/limits and link to actual
  documentation/evidence. Sitemap entries use final canonical public page URLs
  and the real deployment base path; no tab fragments, 404, or backend endpoints.
- These are planned static utility files, not extra content pages or published
  assets. Keep the six-page proposal and compact navbar. Build/deployment link
  and content validation remain in P8/P9; no hosting/indexing outcome is claimed.

## LLM overview content draft - 2026-10-18

- The user supplied Cierto's actual file screenshot to clarify the content:
  plain Markdown with a title, blockquoted overview, key facts, and categorized
  links with descriptions. Match that structure for Relevo.
- Created repository-root `llms.txt` as a readable source draft using current
  verified behavior and existing repository docs/evidence links. It explicitly
  identifies the website as still in design and the verification as dated.
- The source draft is not a published website asset. Refresh release status and
  site links when the frontend exists, and publish the maintained source at the
  footer destination. Sitemap and hosted utility validation remain pending.

## Website walkthrough proposal - 2026-10-18

- The user requested a complete design/visitor walkthrough before building.
  Expanded `design.md` with proposed global presentation, homepage narrative,
  Engine workspace/step behavior, supporting page reading order, and responsive,
  reduced-motion, loading, error, and copy-control behavior.
- These details elaborate the proposal; they are not new user approvals or
  verified UI. The accepted Engine/Replay merge and all reference roles remain.
  Palette, fonts, logo/final illustration, motion specifications, and P8.1 are
  still open. No frontend scaffold or deployment has begun.

## Palette recommendation - 2026-10-18

- The user requested a colour recommendation. Proposed warm chalk, graphite,
  and burnt orange: light background `#F4F1EA`, dark background `#14191D`, light
  accent `#B84322`, dark accent `#FF9A72`. Supporting/state roles are in `design.md`.
- A conversation palette preview shows the exact colours on both surfaces.
  Fourteen intended opaque text pairs were calculated (minimum 4.81:1); this
  does not replace UI accessibility checks. Palette remains a proposal, not an
  accepted visual decision or frontend implementation. P8.1 stays open.

## Accepted pixel/ASCII motif - 2026-10-18

- The user explicitly wants Griffin's pixelated landing-page effect as part of
  Relevo's direction. Browser inspection identifies its ASCII/glyph-pattern
  canvas banner. Add this motif alongside the exploded-view inspiration.
- `design.md` proposes a dedicated hero-edge band, original code-like glyphs,
  sparse transition echoes, Relevo's own colour tokens, decorative-only meaning,
  pause/reduced-motion/static modes, and bounded rendering paused offscreen.
- The motif is accepted; placement, renderer, animation parameters, and palette
  remain proposals. No frontend effect or performance/accessibility result is
  claimed. Preserve Cierto's structure/light-dark chapters and Etched's footer.

## Typography recommendation - 2026-10-18

- The user asked about fonts. The palette fragment currently inherits the host
  interface font, with system monospace for hex labels; it does not demonstrate
  chosen website typography.
- Proposed Barlow Condensed for major headings, Instrument Sans for body/UI,
  and IBM Plex Mono for code/technical labels/ASCII glyphs. Official project
  sources confirm OFL licensing. Record roles/weights and future self-hosted
  delivery in `design.md`; no separate PC font installation is required.
- These are recommendations, not accepted choices or installed font assets.
  Typography specimens/final sizing and P8.1 remain pending at this historical checkpoint.

## Authorized frontend build and local verification - 2026-10-18

- The required frontend conversation is complete. After discussing structure,
  palette, fonts, original exploded-view animation, and stack, the user explicitly
  said to start building and then continue. This authorizes Phase 8 and supersedes
  the earlier stop-before-frontend boundary. Preserve the historical proposals
  above as discussion checkpoints, not the current implementation status.
- Implemented six content pages: Home, Engine (Flow/Replay tabs), Results, Docs,
  About, Privacy; plus a 404 and static utility files. Header: Engine, Results,
  Docs, GitHub. Footer: Product, Evidence, Build, About with `llms.txt` and Sitemap.
- User-pinned reference roles remain Cierto's structure/light-dark chapters,
  Griffin's breakdown/ASCII inspiration, Etched's schematic footer. The selected
  implementation baseline is chalk/graphite/burnt orange with self-hosted Barlow
  Condensed, Instrument Sans, IBM Plex Mono. Original SVG/Canvas assets require no
  external 3D model or desktop design application.
- React/JavaScript/Vite/CSS implementation is in `frontend`. Six generated HTML
  entries support static direct routes; default production base `/Relevo/` and
  intended canonical origin `https://tirthpanchori.github.io/Relevo/` are configured
  for later hosting. This URL is intended, not verified published hosting.
- A project-local official Node 24.22.0 runtime was downloaded and SHA256 checked.
  `scripts/frontend.ps1` uses/prepares it without a machine-wide installation.
  Locked npm dependencies are installed. Production build and four raw-data/
  artifact checks pass. Nine browser checks pass (29.3s), including six pages at
  1440/390/320px, tab/deep-link controls, replay provenance, hidden/reduced motion,
  filters, error recovery, Canvas suspension, and automated WCAG A/AA checks.
  Report: `artifacts/verification/frontend-browser.json`. Finish review and the
  shipped design-system record remain pending at this checkpoint; P8.5 stays open.
- Replay reads static sanitized committed events; test interventions and untimed
  harness observations stay separate. No API request, public token, live mutation
  control, analytics script, or external font request is added. Results summaries
  derive from raw retained runs and preserve experiment/revision limitations.
- Backend source/semantics remain unchanged. Hosted frontend CI, public deployment,
  clean-clone frontend verification, and Phase 9 backup/restore remain unverified.

## Phase 8 closeout - 2026-10-18

- P8.1-P8.5 are complete locally. After the review fix batch, ten Playwright checks
  pass in 31.9s and the four data/artifact checks pass. Footer utilities are directly
  retrievable, the sitemap parses as XML with six expected URLs, and the 404 works.
- The reviewer scored both requested fixes resolved: readable 14px Replay test
  conditions and a shared manual layer-selector group beside the diagram. The
  final disposition is ship at that fix-list scope, not whole-surface certification.
  Missing separate QUALITY BAR cards and a standalone seed-roll record are disclosed
  in `.impeccable/review/finish-review.md`.
- `design.md` now records actual shipped tokens/components/motion/responsive rules;
  `.impeccable/design.json` is the schema-v2 companion. The complete earlier design
  discussion is preserved in `artifacts/design/discussion-history.md`.
- `artifacts/verification/frontend-local.json` records local tooling, test/review
  evidence, and frontend source hashes. `scripts/frontend.ps1 build` works with
  the project-local runtime. No additional PC application was needed.
- The next milestone is Phase 9: clean-clone frontend checks, hosted frontend CI,
  operational backup/restore, and verified free-only hosting. Nothing is published
  or provisioned by the local Phase 8 completion.

## Structural redesign requested - 2026-10-19

- The user rejected the original frontend's structure and supplied a screenshot
  of the crowded three-column lifecycle. They explicitly request a fresh Griffin
  study using Playwright CLI, frontend Taste, and Impeccable; section-by-section
  rebuilding; less repeated exploded artwork; visible pixel art; fewer Engine
  CTAs; consistent button treatment; and smooth FAQ opening/closing.
- The structural revision preserves the six routes, palette/font assets and
  backend truth. Home gets an interactive ownership illustration, one compact
  exploded architecture section, a continuous actual recovery record replacing
  the duplicate lifecycle/recovery blocks, evidence/limits, FAQ, and Docs ending.
  Flow gets a flat responsibility path; Replay gets recorded assignment bars.
- The old review is not acceptance of this revision. The fresh full review found
  one selected-filter visibility issue; it was fixed and scored resolved, ship at
  fix scope. Four data/artifact and fifteen browser checks pass. The shipped
  design-system record is updated in `design.md` and `.impeccable/design.json`;
  the 18 October system is archived. Deployment remains deferred.
- Research/argument/contract: `artifacts/design/revision-2026-10-19.md`.
  Taste selected product-performs, seed 40997419, keeping brand palette/type.
  The user-pinned software art and grouped schematic footer override unrelated
  photo/logo/animation quotas and conflicting catalogue slots.

## Requested development tools installed - 2026-10-19

- The user requested Graft/Trail Code and Anatomy from GitHub. Resolved as
  `trailhq/Trail-Code` (formerly Graft) and `wheresryan22/anatomy` (interactive
  isometric illustration skill), consistent with the frontend work.
- Official `@trailhq/trail-code@0.23.0` is installed in ignored
  `.tools/trail-code`. `scripts/trail.ps1` invokes it through the existing portable
  Node runtime, with usage telemetry disabled and no paid model calls. Its
  deterministic build mapped 98 supported Python/JavaScript/JSX files into 579
  nodes and 1,831 edges. Scope: backend/src, backend/tests, frontend/src, scripts.
  The actual cache is `graft/`, ignored. No automatic global hooks, session-history
  ingestion, MCP registration, or hosted workspace was configured by this install.
- Anatomy was installed with the system skill-installer from Git revision
  `1482e8469b0a9e0d8cc18ea2740a01423d29ae80` into
  `C:/Users/panch/.codex/skills/anatomy`. Six geometry-projection checks pass.
  It becomes available on the next turn. Installing it did not change site art.
- Neither tool required a separate PC application or restart. The website remains
  independent of these development tools and preserves the INR 0 hosting constraint.

## Frontend revision priority and requested tools - 2026-10-18

- The user says substantial frontend design modifications are needed. Revise the
  frontend with their direction before continuing deployment; the original
  Phase 8 verification describes the implemented baseline, not acceptance of its
  final visual design. Specific requested visual changes are still to be supplied.
- The user requested Playwright CLI and the frontend Taste skill from GitHub.
  Installed `@playwright/cli@0.1.22` as an exact frontend development dependency;
  its official repository is `microsoft/playwright-cli`. Version/help checks pass.
  Root invocation: `./scripts/frontend.ps1 browser --help`, using the portable Node
  runtime. A fresh headless Chrome session successfully opened `about:blank`,
  evaluated the document title, and closed. The existing Playwright test runner
  still reports version 1.64.1 and remains a separate tool.
- Installed Codex skills in `C:/Users/panch/.codex/skills` using the system
  skill-installer helper: `design-taste-frontend` from
  `Leonxlnx/taste-skill`, path `skills/taste-skill`, revision
  `f624f37a8c650b9cc550253104925efe4c8de246`; and `playwright-cli` from
  `microsoft/playwright-cli`, path `skills/playwright-cli`, revision
  `b85c7a736bb473bf55b584e54a09ffa698d6d871`. They become available on the next
  turn. This Taste skill is for frontend design; the pre-existing ECC Taste skill
  describes music/video creative direction and is a different skill.
- No site design, backend behavior, or deployment changes were made by installation.

## Production desktop milestone — 2026-10-21

- P8.D3d-D5 complete locally: the accepted demo structure is integrated across
  all six main pages, with 76/68/40px display hierarchy, lime recover, live pixels,
  four explanatory Anatomy assemblies and coordinated Motion/CSS feedback.
- Eleven desktop checks pass at 1440/1920, four data/artifact checks pass, and
  seven desktop axe scans report zero violations. Fresh full review requested
  one heading correction and current design records; both scored resolved in
  the final fix-scoped ship verdict. Evidence: artifacts/verification/production-desktop.json.
- Local preview at port 4173/Relevo is the production site. The demo and previous main
  are retained as dated comparisons. Backend APIs/recordings are unchanged.
- Stop for user desktop review. P8.D6 responsive work, hosted CI and Phase 9
  deployment/operational work remain unverified. No paid service or new PC app.

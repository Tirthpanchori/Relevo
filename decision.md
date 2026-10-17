# Relevo technical decisions

Recorded: 2026-10-16 (Asia/Calcutta).

This is the canonical rationale log. Initial entries consolidate the accepted direction in [PROJECT_MEMORY.md](PROJECT_MEMORY.md); implementation refinements are identified explicitly. **Accepted** means a design baseline, not a verified capability. D001-D014 capture the original documentation baseline; D015 onward record implementation choices. Current execution status and evidence belong in [implementation-plan.md](implementation-plan.md).

For a consequential new choice, append an entry with an ID, date, status, context, decision, alternatives, consequences, and verification. Use `Proposed`, `Accepted`, `Deprecated`, or `Superseded by Dxxx`. Preserve the original rationale when replacing a decision and link its successor. Routine naming/formatting changes do not need entries. All initial entries below were recorded on the date above.

| ID | Decision | Status |
|---|---|---|
| [D001](#d001---backend-correctness-before-frontend) | Backend correctness before frontend | Accepted |
| [D002](#d002---python-engine-with-independent-runtime-processes) | Python engine with independent runtime processes | Accepted |
| [D003](#d003---postgresql-is-the-durable-authority) | PostgreSQL is the durable authority | Accepted |
| [D004](#d004---separate-jobs-attempts-and-committed-events) | Separate jobs, attempts, and committed events | Accepted |
| [D005](#d005---atomic-claims-and-short-transactions) | Atomic claims and short transactions | Accepted |
| [D006](#d006---leases-fencing-and-database-time) | Leases, fencing, and database time | Accepted |
| [D007](#d007---idempotent-submission-and-outcome-reports) | Idempotent submission and outcome reports | Accepted |
| [D008](#d008---independent-recovery-with-bounded-retries) | Independent recovery with bounded retries | Accepted |
| [D009](#d009---supervised-registered-handler-processes) | Supervised registered handler processes | Accepted |
| [D010](#d010---execution-may-repeat-business-effects-need-protection) | Execution may repeat; business effects need protection | Accepted |
| [D011](#d011---small-http-interface-and-trusted-cluster-security) | Small HTTP interface and trusted-cluster security | Accepted |
| [D012](#d012---real-database-fault-tests-and-measured-performance) | Real database fault tests and measured performance | Accepted |
| [D013](#d013---javascript-frontend-with-traceable-recorded-replay) | JavaScript frontend with traceable recorded replay | Accepted |
| [D014](#d014---free-only-delivery-with-local-reproducibility) | Free-only delivery with local reproducibility | Accepted; hosting provider unresolved |
| [D015](#d015---locked-environments-and-packaged-migrations) | Locked environments and packaged migrations | Accepted |
| [D016](#d016---explicit-submission-normalization-and-bounds) | Explicit submission normalization and bounds | Accepted |
| [D017](#d017---job-first-locking-and-guarded-ownership-writes) | Job-first locking and guarded ownership writes | Accepted |
| [D018](#d018---persisted-outcome-acknowledgments-and-positive-retry-jitter) | Persisted outcome acknowledgments and positive retry jitter | Accepted |
| [D019](#d019---database-enforcement-of-one-running-attempt) | Database enforcement of one running attempt | Accepted |
| [D020](#d020---monotonic-worker-supervision-with-bounded-io) | Monotonic worker supervision with bounded I/O | Accepted |
| [D021](#d021---transactional-bounded-expiry-recovery) | Transactional bounded expiry recovery | Accepted |
| [D022](#d022---explicit-async-client-and-immutable-retries) | Explicit async client and immutable retries | Accepted |
| [D023](#d023---independent-business-transactions-and-actual-recordings) | Independent business transactions and actual recordings | Accepted |
| [D024](#d024---isolated-tcp-faults-and-process-crash-proof) | Isolated TCP faults and process-crash proof | Accepted |

## D001 - Backend correctness before frontend

**Origin:** explicit user direction and saved project scope.

**Context:** the project's value is explaining and proving coordination/recovery behavior. Visual polish cannot establish those guarantees.

**Decision:** build contracts, persistence, claims, workers, recovery, fault evidence, and benchmarks before frontend implementation. Require the backend gate in the implementation plan. Maintain the four project documents as the implementation evolves.

**Alternatives:** build the UI first (gives early visuals but no engine evidence); implement a generic task CRUD API (smaller but misses the coordination problem).

**Consequences:** backend work is independently demonstrable through a client/CLI; the frontend starts later and must reflect actual evidence. Keep the 6-8 week scope focused rather than adding infrastructure for its own sake.

**Verification:** Phase 7 gate and traceable tests/recordings before Phase 8.

## D002 - Python engine with independent runtime processes

**Origin:** saved stack and architecture; module boundaries are implementation refinements.

**Context:** the API, recovery loop, and execution processes need to fail/restart independently while sharing one coordination model.

**Decision:** use Python 3.13, FastAPI/Pydantic, SQLAlchemy with Psycopg, Alembic, and HTTPX. Keep one backend codebase with thin API handlers, transactional engine operations, database code, worker supervision, scheduler, and registered handlers. Run API, workers, and scheduler as separate processes/services. Use Docker Compose and GitHub Actions.

**Alternatives:** microservices with separately owned stores (more coordination/deployment work); an API background thread as the only worker/scheduler (couples execution and recovery to HTTP process lifetime); Celery (hides mechanics this project is intended to implement).

**Consequences:** shared engine logic reduces divergent state transitions; process separation requires explicit configuration and lifecycle tests. Critical coordination SQL remains visible even when SQLAlchemy manages ordinary access and connections.

**Verification:** independent restarts, shared engine tests, and a clean Compose startup. Pin compatible dependency versions during implementation rather than treating this log as a lockfile.

## D003 - PostgreSQL is the durable authority

**Origin:** saved engine guarantee; explicit durability settings refine its implementation.

**Context:** a returned job ID must represent committed work. Splitting authoritative queue state across memory and another store introduces additional failure windows.

**Decision:** use PostgreSQL 18 for job state, attempts, scheduling eligibility, and transition history. Acknowledge writes only after transaction commit. Preserve `fsync`, `full_page_writes`, and synchronous local commit; use persistent storage. Do not add a separate broker in v1. PostgreSQL documents the crash-durability tradeoff when these settings are disabled. [PostgreSQL WAL settings](https://www.postgresql.org/docs/18/runtime-config-wal.html)

**Alternatives:** an in-memory queue (loses accepted work on restart); a separate broker/database combination (adds cross-system consistency work); weaker durability for better benchmarks (contradicts the acceptance contract).

**Consequences:** transactions give one durable decision point; database availability and storage integrity bound the whole engine. A single database is not a high-availability or destroyed-disk recovery solution. Database downtime must not produce false submission success.

**Verification:** commit/rollback, lost-response, and persistent-volume restart tests; record durability settings with benchmarks.

## D004 - Separate jobs, attempts, and committed events

**Origin:** saved data model; ordering/constraints are implementation refinements.

**Context:** a job can execute several times. Overwriting its worker/error fields would erase why recovery occurred.

**Decision:** `jobs` holds the logical request/current state; `attempts` records each execution and ownership; `job_events` records committed transitions. Commit affected state, attempt, and event rows together. Enforce valid states, unique attempt numbers/tokens per job, and stable per-job event ordering. Keep a separate business-effect ledger for the demonstration.

**Alternatives:** one mutable row only (poor recovery evidence); full event sourcing (adds reconstruction/schema complexity beyond v1); logs as the history (can disappear or describe rolled-back work).

**Consequences:** state and durable history agree; events are an audit trail rather than the sole source used to reconstruct state. Storage grows with attempts/events; no deletion/retention policy is implemented in v1, and submission-key bindings remain with jobs.

**Verification:** rollback atomicity, event ordering, invariant queries, and no extra transition on replayed reports.

## D005 - Atomic claims and short transactions

**Origin:** saved claiming strategy; lock ordering is an implementation refinement.

**Context:** independently polling workers must not create simultaneous valid ownership for the same job.

**Decision:** claim eligible work with explicit `FOR UPDATE SKIP LOCKED` SQL. Create ownership/attempt/event and update the job in one short transaction. Use consistent lock ordering across all engine operations, serializing changes on the job row. Release locks before task execution. PostgreSQL describes `SKIP LOCKED` as suitable for concurrent queue consumers. [PostgreSQL locking clause](https://www.postgresql.org/docs/18/sql-select.html#SQL-FOR-UPDATE-SHARE)

**Alternatives:** select then update without transactional protection (races); hold a lock throughout the task (long transactions); an in-process mutex (does not coordinate independent processes).

**Consequences:** workers can skip contested candidates; strict FIFO ordering/fairness is not guaranteed. Database contention remains measurable. Every ownership-changing path must follow the same locking discipline.

**Verification:** synchronized competing claims, crash after commit, and races with heartbeat/report/recovery.

## D006 - Leases, fencing, and database time

**Origin:** saved ownership design; post-lock time evaluation refines correctness.

**Context:** a disconnected worker may continue executing after another attempt becomes eligible. Worker identity alone cannot distinguish those attempts.

**Decision:** each attempt has a worker identity, an increasing per-job fencing token, and an expiry. Only the matching current, unexpired attempt can renew or report a new outcome. Check authoritative time in PostgreSQL after obtaining the required locks; use a fresh `clock_timestamp()` sample for ownership decisions rather than a timestamp frozen before a wait. `now()` is transaction-start time in PostgreSQL. [PostgreSQL current-time functions](https://www.postgresql.org/docs/18/functions-datetime.html#FUNCTIONS-DATETIME-CURRENT)

**Alternatives:** trust client clocks (clock disagreement); worker ID without a token (cannot fence earlier attempts); accept late completion until the scheduler runs (makes expiry dependent on scan timing).

**Consequences:** stale processes cannot overwrite engine state. Physical execution can still overlap during failures; fencing does not roll back external effects. The shared database clock must remain operationally sane; local elapsed-time supervision uses a monotonic clock.

**Verification:** stale heartbeat/outcome, expiry before recovery, reassignment, lock-wait-across-expiry, and competing recovery/report tests.

## D007 - Idempotent submission and outcome reports

**Origin:** saved API guarantees; normalization and replay identity are implementation refinements.

**Context:** a response may disappear after its transaction commits. The caller cannot infer failure from a timeout.

**Decision:** require submission idempotency keys backed by a unique database constraint. Canonicalize task-affecting request fields; same key/content returns the existing job, changed content conflicts. Keep generated immediate scheduling timestamps out of that request fingerprint. Store normalized terminal reports so the matching attempt identity can replay an identical committed report even after expiry or a later attempt, without a new transition. Reject conflicting reports.

**Alternatives:** generate a new job on every retry (duplicates work); deduplicate only in memory (fails across restart); reject all terminal-report replays (leaves committed outcomes ambiguous).

**Consequences:** callers must preserve keys and report content across retries. A replay acknowledges historical success; it never restores ownership or mutates a newer attempt. Submission idempotency does not deduplicate different keys or repeated business effects.

**Verification:** concurrent inserts, normalized requests, changed schedules/payloads, lost submission/report responses, and repeated failure reports after retry/reassignment.

## D008 - Independent recovery with bounded retries

**Origin:** saved lifecycle and timing defaults.

**Context:** jobs must stay accounted for when workers disappear, without retrying permanently broken work forever.

**Decision:** use `pending -> running -> succeeded/failed`. Retryable failures and expired attempts return jobs to `pending` with future availability, unless the total-attempt budget is exhausted. Permanent failures become `failed`. Delayed jobs remain pending until eligible. Terminal jobs cannot reset in v1. Run a separate transactional recovery scheduler; use configurable bounded exponential backoff and jitter.

| Default | Value |
|---|---|
| Lease duration | 15 seconds |
| Heartbeat interval | 5 seconds |
| Recovery scan interval | 2 seconds |
| Total attempts, including first | 3 |
| Task execution timeout | 60 seconds |
| Payload/result limit | 64 KB each; serialized-byte convention resolved in [D016](#d016---explicit-submission-normalization-and-bounds) |

**Alternatives:** unlimited immediate retries (retry storms/poison jobs); recovery only at API startup (misses later expiry); worker-memory timers as the schedule (lost on restart).

**Consequences:** recovery needs scheduler/database availability and consumes attempts even when an assigned worker never starts. Recovery time includes remaining lease, scan delay, retry backoff, and queue delay; it is not an exact two-second promise. Configurable timings and injected randomness keep tests controlled.

**Verification:** delayed boundaries, poison-job isolation, three-attempt exhaustion, overlapping scans, scheduler restart, and race tests.

## D009 - Supervised registered handler processes

**Origin:** saved runtime model; portable process startup refines implementation.

**Context:** a slow/stuck handler must not prevent lease renewal or force the supervisor to wait forever on ownership loss.

**Decision:** each worker runs one registered handler in a child process. The supervisor communicates through HTTPX, renews the lease, enforces timeout/size limits, and stops/reaps the child on rejected ownership, unconfirmed renewal, or timeout. Start with hashing, timed work, and configurable transient failures. Use explicit `spawn` process context, safe module entry points, and process-local resources for consistent Windows/Linux behavior. [Python multiprocessing documentation](https://docs.python.org/3.13/library/multiprocessing.html#contexts-and-start-methods)

**Alternatives:** execute arbitrary uploaded code (out of scope); run handlers inside the heartbeat loop (blocks supervision); rely on interrupting a Python thread (does not provide the required process lifecycle boundary).

**Consequences:** per-task process startup adds overhead and argument/result serialization constraints. Process isolation is not a sandbox for hostile code. Abrupt supervisor death can leave work running temporarily; tests must distinguish graceful cleanup, container death, and parent-only death. Engine fencing and business idempotency remain required.

**Verification:** cross-platform startup, timeout, failed renewal, bounded process communication, child cleanup, and measured short-task overhead.

## D010 - Execution may repeat; business effects need protection

**Origin:** saved execution guarantee and required effect demonstration.

**Context:** a handler can commit an effect, then crash before its completion report commits. Recovery cannot know whether that external effect happened.

**Decision:** explicitly allow repeated execution under recovery; do not claim exactly-once execution/effects or instruction-level resumption. Keep retries bounded, so eventual successful execution is not unconditional. Demonstrate the ambiguity with an independently committed business-effect ledger, then show a unique stable business-operation key protecting the effect transaction.

**Alternatives:** call retries exactly-once (false); deduplicate only the completion endpoint (does not protect the earlier effect); use attempt IDs as business keys (changes on retry).

**Consequences:** handler authors own effect safety. Protection applies only to the operation/store that enforces the key; an email/payment/remote API needs its own deduplication protocol. An executor token protects state only unless the effect destination explicitly enforces it.

**Verification:** commit an effect and lose completion; show duplicate unprotected effects and one protected effect across multiple attempts.

## D011 - Small HTTP interface and trusted-cluster security

**Origin:** saved exact endpoints and trusted-cluster model; bearer transport refines implementation.

**Context:** a narrow API keeps the coordination behavior testable and usable without a frontend. V1 is not a tenant-isolated public execution platform.

**Decision:** preserve all ten exact routes in [project memory](PROJECT_MEMORY.md#agreed-http-endpoints) and the [implementation contract](implementation-plan.md#http-contract-to-preserve). Validate with Pydantic. Require an environment-provided shared bearer token for job/internal access and protect metrics. Keep minimal health responses. Workers use HTTP rather than directly mutating engine tables; the scheduler uses the same transactional engine operations locally. Provide a Python client/CLI.

**Alternatives:** add a full account/RBAC product (outside v1); browser-accessible worker controls with an embedded token (exposes privileged credentials); let every worker implement its own engine SQL (duplicates coordination logic).

**Consequences:** trusted clients with the token share privileges; worker IDs are coordination identifiers, not independently authenticated identities. Keep the database private, never ship the token in static assets, and use TLS for any nonlocal authenticated access.

**Verification:** route-contract and authentication tests, secret-free bundles/fixtures/logs, and demonstrable CLI workflows.

## D012 - Real database fault tests and measured performance

**Origin:** saved test/observability strategy; durable-versus-runtime telemetry distinction refines interpretation.

**Context:** mocks and happy-path demos cannot establish transaction/locking behavior; more workers do not automatically imply more throughput.

**Decision:** use pytest against real PostgreSQL for coordination, synchronized checkpoints for races, Toxiproxy for controlled network faults, and repeatable crash scenarios. Add structured logs, OpenTelemetry, Prometheus/Grafana, and the agreed metrics. Benchmark identical workloads with 1, 3, and 5 workers, repeated runs, raw data, environment details, and one measured improvement.

**Alternatives:** SQLite as proof of PostgreSQL locking (different semantics); arbitrary sleeps as race synchronization (unreliable evidence); invented throughput or percentages (unverifiable).

**Consequences:** tests need infrastructure and bounded timing; CI must reproduce essential scenarios. Durable `job_events` establish transition history; in-process counters/traces can reset or miss observations. Avoid IDs in metric labels and secrets/payloads in telemetry.

**Verification:** Phase 6 failure matrix, Phase 7 benchmark artifacts, and the backend readiness gate. No numerical performance claims until measurements exist.

## D013 - JavaScript frontend with traceable recorded replay

**Origin:** explicit JavaScript preference and saved frontend direction.

**Context:** a portfolio visitor needs to understand failures and evidence even when a free live engine is unavailable.

**Decision:** use React, JavaScript (`.jsx`/`.js`), Vite, and CSS after the backend gate. Build an architecture/lifecycle explanation, attempt timeline, guarantees/limits, actual benchmark presentation, quickstart, and repository links. Public interaction replays sanitized real test recordings with source/capture metadata; it does not call privileged worker controls. Final visual direction is still unresolved.

**Alternatives:** TypeScript (contradicts the user's choice); a full administration dashboard (outside v1); unlabeled synthetic or recorded events presented as live execution (misrepresents the evidence).

**Consequences:** the explanation works independently of engine uptime. Regenerate recordings when relevant behavior changes, show which revision they describe, and clearly label replay/annotations. Support keyboard operation, reduced motion, responsive layouts, and static diagram comprehension.

**Verification:** recording provenance, accessible replay controls, production build, and secret-free assets that work with the backend offline.

## D014 - Free-only delivery with local reproducibility

**Origin:** explicit budget change superseding the earlier paid-hosting proposal.

**Context:** the recurring budget is INR 0; time-limited credits do not meet that requirement. A live deployment may be constrained by free capacity.

**Decision:** ship the full engine locally through Compose. GitHub Pages on its free address is the proposed static frontend host. Consider Oracle Cloud Always Free for an optional live engine only after verifying current eligibility, terms, resources, and availability. No hosting resource has been provisioned, and provider suitability is not yet verified. If free capacity is unavailable, retain local execution and recorded public evidence.

**Alternatives:** the earlier INR 1,000/month plan or a paid VM/database/domain (superseded and outside authorization); trial credits as ongoing free hosting (do not meet the budget).

**Consequences:** no guaranteed public live uptime or cloud capacity. Static explanation and recordings must stand alone. Verify provider terms at provisioning time and document the actual result rather than promising free resources.

**Verification:** reproducible clean-checkout setup, recorded demo, free-host eligibility review before deployment, and actual configuration/cost boundary review if a live engine is provisioned.

## D015 - Locked environments and packaged migrations

**Date:** 2026-10-16. **Status:** Accepted. **Origin:** Phase 1 implementation.

**Context:** Windows development and Linux containers need reproducible dependencies and the same schema history. Migration lookup must also work after installing the Python package rather than only from a source checkout.

**Decision:** use uv 0.13.1 with a committed cross-platform `backend/uv.lock`, Python 3.13, and digest-pinned Python/PostgreSQL images. Use synchronous SQLAlchemy/Psycopg for short transactions in FastAPI's synchronous route thread pool. Package migrations under `relevo/db/migrations`; run them in a separate Compose step before API startup. Readiness checks the migration head and durability settings. Generate ignored local credentials once; isolate integration tests in their own `*_test` database.

**Alternatives:** unpinned installation (version drift); blocking synchronous database calls in async handlers (blocks the event loop); application-startup `create_all` (no versioned schema evolution); source-relative migrations outside the installed package (breaks packaged startup); tests against development tables (risks application data).

**Consequences:** upgrade dependencies/images deliberately with verification. Source and container paths differ without changing migration identity. Local development uses trusted local database credentials, not a finalized cloud access policy. The resolved Starlette TestClient requires `httpx2`, installed only in the dev group; worker communication remains HTTPX as agreed.

**Verification:** 47 passing checks on Windows and Linux, Alembic upgrade/downgrade and drift checks, and healthy installed-package Compose startup. GitHub Actions is configured; its hosted run is unverified until a remote exists. The PostgreSQL 18 volume mount follows the [official image's persistence layout](https://hub.docker.com/_/postgres).

## D016 - Explicit submission normalization and bounds

**Date:** 2026-10-16. **Status:** Accepted. **Origin:** Phase 1/2 contract implementation; resolves D008's byte convention.

**Context:** JSON formatting, key ordering, and equivalent timezone representations must not create accidental conflicts, while different work must not silently reuse an idempotency key. Validation must happen before persistence.

**Decision:** fingerprint a normalized request using SHA-256 over sorted-key, compact UTF-8 JSON with unescaped Unicode and finite numbers. Normalize explicit `run_at` to UTC; omitted/null means immediate, and generated database time is excluded from the request fingerprint. Preserve JSON numeric representation (`1` and `1.0` are distinct requests under this encoding). Require 1-200 ASCII key characters from letters, digits, `_`, `.`, `:`, and `-`. Enforce 65,536 canonical payload bytes, at most 64 nesting levels, and a 1 MiB raw POST body cap before decoding; reject null characters and invalid Unicode that JSONB cannot store. Results will use the same byte convention when outcomes are implemented.

**Alternatives:** hash raw HTTP bytes (formatting changes conflict); include effective current time for immediate requests (every retry conflicts); count characters (miscounts UTF-8); silently accept a changed request (binds a key to ambiguous work).

**Consequences:** clients retain their original key/content; equivalent key order and timezones replay safely. This is a specified application encoding, not a claim to implement a universal JSON canonicalization standard. Submission uses `INSERT ... ON CONFLICT DO NOTHING` followed by a fresh READ COMMITTED query; database uniqueness resolves races, and the job/event transaction commits before a successful HTTP response. Changes to normalization need an explicit compatibility decision.

**Verification:** synchronized duplicate/conflict tests, timezone/key-order replay, exact multibyte boundaries, invalid/deep JSON and raw-body limits, forced rollback/commit failures, and a dropped response after committed submission.

## D017 - Job-first locking and guarded ownership writes

**Date:** 2026-10-16. **Status:** Accepted. **Origin:** Phase 3 implementation, refining D005/D006.

**Context:** a request may start before lease expiry but wait on another transaction's lock until the lease is already expired. A check based on transaction-start time would accept stale ownership.

**Decision:** claims select an eligible pending job with ordered `FOR UPDATE SKIP LOCKED`; every renewal/report locks its parent job before locking the attempt. An unlocked attempt lookup obtains only the immutable parent ID. Read fresh `clock_timestamp()` after locks and also guard the final attempt update with `lease_expires_at > clock_timestamp()`. PostgreSQL documents the distinction between transaction-start and actual current time in its [time functions](https://www.postgresql.org/docs/18/functions-datetime.html#FUNCTIONS-DATETIME-CURRENT), and row locks serialize conflicting updates as described in [explicit locking](https://www.postgresql.org/docs/18/explicit-locking.html). Recovery must reuse this order in Phase 5.

**Alternatives:** test ownership before waiting (can become stale); lock attempts before jobs in some operations (inconsistent ordering risks deadlock); permit a report until the next scheduler scan (weakens expiry).

**Consequences:** acceptance is decided at the guarded state write while ownership is valid; commit/HTTP delivery can occur later. No handler executes under these locks. Heartbeats never shorten an existing lease, even after configuration changes, and do not append a state-transition event. Only outcomes/claims increment the transition sequence. A past-lease running attempt stays fenced even before recovery exists.

**Verification:** real lock contention is observed through `pg_stat_activity`, then a controlled deadline crosses the waiting transaction's start time. Heartbeat/completion/failure must all reject it. Additional tests move expiry at the final SQL-write boundary, race claimers/reports/renewals, and verify transactional rollback and deterministic candidate ordering.

## D018 - Persisted outcome acknowledgments and positive retry jitter

**Date:** 2026-10-16. **Status:** Accepted. **Origin:** Phase 3 implementation, refining D007/D008.

**Context:** failure reporting needs to choose a bounded retry now, before the independent recovery scheduler exists. A lost response must not schedule the same failure again or change a newer attempt's state.

**Decision:** store a fingerprint including report kind, worker, token, and normalized content alongside the accepted response. An identical report from that attempt identity returns its original historical acknowledgment, including its original state/availability, after expiry or reassignment. A changed report or different identity conflicts. A job lookup supplies current state. Preserve acknowledgments for already accepted submission/report content when only a configured payload/result admission limit is reduced; new over-limit work is still rejected within the absolute raw request cap.

**Retry policy:** the attempt budget stored on the job remains authoritative. For retryable failures with budget remaining, use an exponential ceiling `min(30 seconds, 1 second * 2^(attempt_number - 1))` by default. Choose a delay uniformly between half and all of that ceiling (equal jitter). Base/cap are configurable; randomness is injectable in tests. This creates a strictly positive retry delay. Permanent or exhausted failures are terminal. Date/time settings have finite bounds and millisecond minimums to prevent overflow or rounded-to-zero leases/delays; fencing inputs fit PostgreSQL signed 64-bit integers.

**Alternatives:** reschedule on every repeated failure report (duplicates transitions); return the latest job state as the old report's acknowledgment (loses the original transaction's result); use zero-inclusive full jitter (can retry immediately); make admission limits retroactively invalidate committed acknowledgments (complicates lost-response recovery).

**Consequences:** a historical `pending` acknowledgment can be replayed after the job is running or succeeded; it conveys no ownership. The delay policy is introduced now because failure reporting requires it; scheduler-based expiry recovery remains future work. State, attempt, and event updates commit together, and no success response escapes a failed transaction.

**Verification:** identical/conflicting concurrent reports, lost HTTP report responses, old-report replay after a newer success, total-attempt exhaustion, new admission rejection versus old acknowledgment after limit reduction, and deterministic jitter bounds.

## D019 - Database enforcement of one running attempt

**Date:** 2026-10-16. **Status:** Accepted. **Origin:** migration `0002`, refining D004/D005.

**Context:** job-row locking supplies coordination, but a future buggy mutation path should not be able to insert two running attempts for one job.

**Decision:** add a partial unique index on `attempts(job_id)` where `state='running'`, in a new reversible migration. Preserve migration `0001`. The job's composite current-attempt foreign key continues to ensure that the referenced attempt belongs to that job.

**Alternatives:** rely only on application locking (no independent constraint); rewrite the installed baseline migration (does not upgrade an existing database); index all attempts uniquely by job (would prohibit retries).

**Consequences:** the invariant is stronger than uniqueness of valid leases: an expired attempt still marked running must be closed before another attempt can be created. Phase 5 recovery must close it transactionally. The index adds write/index cost and is included in migration/drift checks.

**Verification:** competing claims and a direct attempted insertion of a second running attempt; migration upgrade/downgrade and metadata comparison against real PostgreSQL.

## D020 - Monotonic worker supervision with bounded I/O

**Date:** 2026-10-16. **Status:** Accepted. **Origin:** Phase 4 implementation, refining D009/D011.

**Context:** a blocking heartbeat or partially written result pipe must not keep a handler alive after ownership becomes uncertain. Worker and database wall clocks can disagree, and a lost terminal-report response must not execute the handler again.

**Decision:** use HTTPX AsyncClient under a total `asyncio.timeout` budget, not just HTTPX's individual network-operation timeouts. The distinction follows [HTTPX timeout semantics](https://www.python-httpx.org/advanced/timeouts/). Claims/renewals add `lease_seconds`; claims add `max_result_bytes`. Start conservative local lease deadlines at request send time plus the returned duration, and adapt heartbeat spacing to the lease. Worker elapsed-time checks use `time.monotonic`, whose clock is shared across local processes in Python 3.13. [Python time documentation](https://docs.python.org/3.13/library/time.html#time.monotonic)

**Child boundary:** use explicit `spawn` with import-safe entry points. Pass task data and bounds only; do not pass connections or HTTP clients. The child removes Relevo cluster credentials from its inherited environment, executes a registered handler, bounds its output, and atomically renames a private result file. The supervisor polls the process, then reads a bounded finished file. This avoids blocking supervision on a partially received pipe message. Both supervisor and child check the execution deadline; result delivery retries reuse the same report without another handler invocation. A parent-liveness watchdog is implemented, and Compose uses init plus a bounded shutdown grace period.

**Alternatives:** a synchronous network call without a total deadline (can delay supervision); compare database expiry to worker wall time (clock skew); read a blocking IPC frame in the heartbeat loop (a stalled writer can block supervision); restart the handler on a lost completion response (duplicates execution unnecessarily).

**Consequences:** per-task process startup and temporary-file I/O have measurable overhead. These are operational process boundaries, not a hostile-code sandbox or hard real-time guarantee. Parent-death/orphan cleanup remains best effort until directly tested. Workers require only API URL/token; their Compose environment omits database credentials. The additive claim/renewal fields require deploying the updated coordinator with this first worker version.

**Evidence:** 137 tests passed on Windows and Linux against PostgreSQL, including real spawned handlers, supervisor heartbeats/timeouts/cleanup, exact report retries, and API/database integration. The installed Compose worker passed hashing/transient-failure smoke checks before/after a worker-only restart with a new identity. Isolated orphan watchdog timing remains unverified; container crash recovery is tracked separately in Phase 5/6.

## D021 - Transactional bounded expiry recovery

**Date:** 2026-10-16. **Status:** Accepted. **Origin:** Phase 5 implementation, refining D005/D006/D008.

**Context:** expiry must be recovered while the API/worker may be unavailable, and more than one scheduler can scan concurrently. A scan snapshot cannot authorize a state change after waiting for locks.

**Decision:** run `python -m relevo.scheduler` as an independent database client. Discover expired current attempts using the existing partial expiry index and `FOR UPDATE OF j SKIP LOCKED`; lock jobs before attempts, re-read current ownership, and use fresh database time plus a final SQL expiry guard. Process at most 100 candidates per transaction by default (configurable 1-1,000). Mark each attempt `expired`, clear current ownership, choose a positively delayed retry or terminal failure using the job's frozen total-attempt budget, and append one `expired` event in the same transaction. Expiry is not a worker report, so it never fabricates a report fingerprint/acknowledgment.

**Operation:** scans wait 2 seconds between batches by default, retry unconfirmed database operations on later scans, and store no cursor or ownership state in process memory. Shared validated backend settings and database connectivity are reused; the scheduler currently receives the backend environment, including an unused shared API token. It does not require a healthy API to recover work. `--once` provides a bounded-batch operational/test command. PostgreSQL transactions and skip-locked row selection make a singleton scheduler lock unnecessary.

**Alternatives:** recover only in API startup (recovery stops with the API); release locks between job/attempt/history changes (partial or racing transitions); count an expiry as a new attempt (incorrect budget); immediately retry without backoff (poison-job churn); keep a process-local scan cursor (restart can strand work).

**Consequences:** a failed batch rolls back as a whole; a lost commit acknowledgment is safe because later scans only select still-running expired ownership. Busy jobs may be skipped, and neither FIFO fairness nor a fixed recovery-time bound is promised. Total recovery includes lease expiry, scan/batch wait, retry delay, queue wait, and execution. Abrupt scheduler termination relies on database rollback rather than graceful completion.

**Verification:** all 152 tests pass on Windows and Linux against PostgreSQL, including six overlapping scanners, bounded batches, locked-row skipping, post-lock revalidation, rollback before event/commit, stale heartbeat/completion races, exhausted budgets, poison-job isolation, scheduler subprocess replacement, and worker completion after a lost claim response. Installed Compose crash smoke passes: kill the worker during execution, pause/resume the scheduler, complete a replacement attempt, and reject the old attempt's late report. Exact commands/limits are recorded in the implementation plan.

## D022 - Explicit async client and immutable retries

**Date:** 2026-10-17. **Status:** Accepted. **Origin:** Phase 6.

Require an explicit coordinator origin and environment-provided token. Public
operations are submit, inspect, attempts, and bounded waiting; the CLI adds a hash
demo. Requests have total async deadlines, bounded responses, no redirects, and no
environment proxy inheritance. Submission freezes canonical bytes and a required
caller-supplied key before awaiting, then retries only uncertain transport/server
failures within a fixed budget. Definitive rejections and invalid responses surface
redacted errors. Tokens have no CLI argument. This avoids a synchronous timeout
implemented with an uncancellable background thread.

**Evidence:** mutation-during-retry, lost committed acceptance, conflict, response
bounds, deadlines, redaction, actual worker completion, and installed CLI demo pass.

## D023 - Independent business transactions and actual recordings

**Date:** 2026-10-17. **Status:** Accepted. **Origin:** Phase 6, refining D010.

Migration `0003` adds `relevo_demo.operations/effects` with no executor foreign keys.
The protected operation's stable key, fingerprint, saved result, and effect commit
together. Concurrent identical requests return that result; changed work conflicts.
Unprotected calls deliberately insert another effect. This shares PostgreSQL but
uses an independent transaction: a logical effect boundary, not separate storage.

An instrumented harness augments hashing with that transaction, loses completion
before coordinator delivery, expires/reassigns ownership, and executes again.
Runtime child credentials stay unchanged. Tests prove duplication, protected
deduplication, concurrent calls, conflict, and atomic rollback. Attempt IDs are
absent from the business fingerprint because they change across retries.

Recordings use actual database snapshots plus labeled interventions, source
hashes/revision, dates, configuration, and schema versions. They omit secrets and
payloads/results and use read-only repeatable read. Missing Git commits remain null
with a source-tree hash. See the [recording guide](artifacts/replays/README.md).

## D024 - Isolated TCP faults and process-crash proof

**Date:** 2026-10-17. **Status:** Accepted. **Origin:** Phase 6.

Use official Toxiproxy 2.13.0 pinned by digest in the test profile. A separate API and
proxies target only the dedicated test database; exposed ports bind to localhost.
Downstream timeout toxics lose responses after actual commits; latency toxics delay
renewal responses; disabling the database proxy cuts pooled connections. Direction
and toxic semantics follow [Toxiproxy documentation](https://github.com/Shopify/toxiproxy#toxics).
The custom command preserves the image's `-host=0.0.0.0` listener argument so other
containers can reach it; host exposure remains loopback-only.

Separate scripts exercise real component restarts and PostgreSQL/worker SIGKILL
with storage retained. Cross-table accounting follows every PostgreSQL test. The
185-test Windows/Linux suite passes; 81 integration checks passed three further
rounds. CI runs the same Compose suite; hosted evidence awaits the new repository.

## D025 - Durable history separated from bounded runtime telemetry

**Date:** 2026-10-17. **Status:** Accepted. **Origin:** Phase 7.

Every API instance owns its Prometheus registry and OpenTelemetry provider.
Explicit operation/SQL spans carry identifiers but no SQL text, parameters,
payloads/results, credentials, raw URLs, or exception messages. Worker requests
propagate trace context to coordinator operations. Optional OTLP export uses a
bounded batch queue and timeout; the engine runs without an exporter. Structured
transition logs are emitted after commit, so rollback cannot advertise a committed
change. Metric labels use fixed operations, states, and route templates; IDs stay
in logs/traces. See [OpenTelemetry instrumentation](https://opentelemetry.io/docs/languages/python/instrumentation/).

Queue delay and claim-to-outcome/expiry duration are also stored with transition
events. Read-only repeatable-read scrapes derive current states, transition/retry
totals, and timing histograms from PostgreSQL. Older events without timings are
excluded rather than backfilled with invented measurements. These aggregates scan
retained history: acceptable for this bounded portfolio workload, but larger
deployments would need measured incremental aggregation. Unavailable database
metrics report `relevo_database_metrics_up=0` and omit values rather than report
false zeros. Runtime HTTP/database/child/supervision counters can reset and are
separate from committed totals; traces/logs can be lost around a process crash.

Child-body timing is private IPC metadata, removed before outcome validation;
invalid optional timing is ignored and cannot change a valid task result. Process
memory metrics exclude child processes; benchmark container samples include them.
Worker/scheduler scrape listeners require the bearer token and are exposed only
inside Compose. Optional digest-pinned Prometheus/Grafana/Jaeger bind user-facing
ports to localhost. Monitoring storage is temporary; PostgreSQL remains the
history authority. Jaeger smoke uses its [stable v3 query API](https://www.jaegertracing.io/docs/2.22/architecture/apis/).

**Evidence:** 195 tests pass on Windows (49.33 seconds) and Linux (32.08 seconds),
including durable metric persistence across API recreation, rollback/log safety,
redaction/cardinality, trace parentage, authenticated scrape access, and malformed
timing metadata. The actual monitoring smoke verifies all three scrape targets,
the provisioned dashboard, and an exported worker/API trace.

## Decisions still open

- Request/response schemas, initial error codes, serialized-byte convention, and dependency pins are resolved in Phase 1/2. Retry backoff/jitter parameters are resolved in D018 and scheduler integration in D021; broader network/crash proof remains for Phase 6.
- Frontend visual direction: establish in Phase 8 from the verified engine story.
- Actual public repository URL and free hosting availability/configuration: resolve in Phase 9. No repository URL or deployment should be invented.

These open details do not block backend failure testing. Broader changes to durability, ownership, effect semantics, or budget require a new linked decision entry.

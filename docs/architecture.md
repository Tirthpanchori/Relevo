# Architecture and technical decisions

Relevo separates durable coordination from task execution. PostgreSQL decides
ownership; Python processes execute registered work. The [behavior guide](how-it-works.md)
walks through a task in plain language.

## PostgreSQL as the authority

Jobs, attempts and transition events live in PostgreSQL. Redis or an in-memory
queue is not required. Acknowledging submission only after commit makes an
accepted job recoverable after process restarts, provided durable storage survives.
State and its event history change within the same transaction.

This keeps coordination in one transactional system. It also makes PostgreSQL
availability and durability settings operational dependencies; local worker
memory cannot establish ownership or replace a backup.

## Jobs, attempts and events

A job records requested work and its eventual outcome. An attempt records one
assignment, including its worker, lease and fencing token. A new attempt preserves
earlier attempts rather than overwriting them. Ordered events record committed
transitions; they are distinct from transient runtime logs and metrics.

Terminal jobs are immutable. The retry budget counts total attempts, including
the first. Recovery restarts the handler rather than resuming its instructions.

## Atomic claims and consistent locking

Eligible jobs are claimed with short `FOR UPDATE SKIP LOCKED` transactions.
Handlers run after those transactions release their locks. Competing workers
can select different jobs without holding database locks throughout execution.

Ownership changes lock the parent job before the attempt. A database constraint
also prevents multiple running attempts for one job. Recovery uses compatible
locking and rechecks state after acquiring locks.

Implementation: [claims and ownership](../backend/src/relevo/engine/ownership.py),
[recovery](../backend/src/relevo/engine/recovery.py),
[database models](../backend/src/relevo/db/models.py).

## Leases, fencing and time

Every new attempt receives an increasing fencing token. New heartbeats and
outcomes require the matching worker, attempt, token and unexpired lease.
PostgreSQL time decides expiry, sampled after locks and checked again at the
guarded ownership write. A request that waits beyond its lease is rejected even
if it began earlier.

Worker supervision uses monotonic elapsed time rather than trusting matching
wall clocks. These checks protect engine state from stale owners. They do not
prevent an isolated old process from physically running or undo its external effects.

## Idempotency and uncertain responses

Submission keys identify normalized requests. Matching retries return the
existing job; conflicting reuse is rejected. Request normalization includes
stable JSON encoding and explicit scheduling-time handling.

An identical report can acknowledge an already committed outcome without a
second transition. A changed report conflicts. Historical acknowledgments do
not grant current ownership; clients inspect the job for current state.

Implementation: [submission](../backend/src/relevo/engine/jobs.py),
[serialization](../backend/src/relevo/engine/serialization.py),
[API contracts](../backend/src/relevo/api/schemas.py).

## Bounded recovery

An independent scheduler scans expired assignments in bounded batches. Expiry,
history and retry scheduling commit together. Retries use positive jittered
exponential backoff and stop at the saved attempt limit. Failed transactions
roll back so a later scan can recover the still-expired assignment.

Recovery depends on the database, scheduler, API and a worker being available.
Neither the scan interval nor a renewable lease is a completion-time guarantee.

## Supervised execution and trust

Each registered handler runs in a child process. Its supervisor handles
heartbeats, deadlines, bounded results and cleanup; unconfirmed renewal stops
the child. This provides process supervision, not an arbitrary-code sandbox.

The shared bearer token grants trusted-cluster access. There are no public user
accounts or tenant boundaries. Task inputs/results and raw HTTP bodies have
validated limits. See [security scope](../SECURITY.md).

## External business effects

Execution can repeat when a handler changes another system but loses its
completion report. Engine fencing does not make external effects exactly once.
A stable business-operation key checked in the same transaction as an effect
can protect that operation; an attempt ID changes on retry and is unsuitable.

The [recording guide](../artifacts/replays/README.md) distinguishes committed
events, test interventions and protected/unprotected effect demonstrations.

## Worker monitor tuning

The supervisor checks for child completion every 50 ms by default. A 5 ms option
was measured with hashing and timed workloads at 1, 3 and 5 workers. It helped
some short-task cases and regressed timed work, so it was not promoted globally.
Process startup and reporting still contribute overhead.

See the [methodology](../benchmarks/README.md),
[repeated comparison](../benchmarks/comparison.md) and
[confirmation](../benchmarks/confirmation.md), including exclusions and confounders.
The retained measurements describe local finite-backlog experiments, not
universal speedups or production capacity.

## Static explanation and reproducible evidence

React and Vite serve six static explanatory pages. Replay uses sanitized real
recordings; Flow is illustrative. Results derives comparisons from retained
measurement files. The site receives no backend token and does not submit live jobs.

Runtime dependencies are locked, migrations ship with the backend package, and
Docker supplies consistent Linux execution. Correctness checks use real
PostgreSQL, concurrent actors, TCP faults and process restarts rather than
substituting an in-memory database. See [testing](testing.md).

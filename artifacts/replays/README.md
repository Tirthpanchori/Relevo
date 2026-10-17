# Actual execution recordings

These JSON files contain real PostgreSQL state/history and explicit test observations.
They support a later labeled replay, not a live engine feed.

| Capture | Source | Evidence |
|---|---|---|
| [Worker crash](worker-crash-recovery.json) | [Smoke script](../../scripts/smoke_recovery.py) | Worker SIGKILL, scheduler pause/resume, expired/successful attempts, rejected stale completion. |
| [Component restarts](component-restarts.json) | [Restart script](../../scripts/smoke_restarts.py) | Acknowledged pending/terminal jobs survive API/database restart and PostgreSQL SIGKILL with storage retained. |
| [Unprotected effect](effect-unprotected.json) | [Effect tests](../../backend/tests/integration/test_effects.py) | Repeated execution creates two unprotected effects. |
| [Protected effect](effect-protected.json) | [Effect tests](../../backend/tests/integration/test_effects.py) | A stable business key protects one effect across attempts. |
| [Additional-expiry diagnostic](additional-expiry-diagnostic.json) | [Smoke script](../../scripts/smoke_recovery.py) | A refresh succeeded on its third attempt; its strict two-attempt assertion rejected the run. Only one death was injected; the extra expiry's cause is unassigned. |

Captures include UTC date, source-file/backend-tree hashes, available Git revision,
configuration, schema/server/Python versions, real identifiers, and committed events.
Missing Git commits are null, never invented. Payloads, results, tokens, DSNs,
business keys, and free-form error messages are excluded. Snapshots use a read-only
repeatable-read transaction.

The effect captures were refreshed against verified commit `d3cc16b` on
2026-10-18. The crash smoke now checks the actual bounded-recovery contract,
including every expired owner's stale report and unchanged terminal state,
instead of promising exactly two attempts; additional expiries are labeled.

The effect harness runs hashing plus a separate business transaction under
instrumented coordinator control. It drops completion before the coordinator
receives it, then forces lease expiry with test SQL and runs recovery. Interventions
are labeled; these recordings do not claim a real child held database credentials
or that a full lease elapsed naturally. The worker-crash recording uses real
container death and the configured lease.

Reproduction from the repository root, with the configured host environment:

```powershell
backend/.venv/Scripts/python.exe -c "from dotenv import load_dotenv; load_dotenv('.env'); import pytest; raise SystemExit(pytest.main(['backend/tests/integration/test_effects.py', '-q', '--recordings-dir', 'artifacts/replays']))"
backend/.venv/Scripts/python.exe -c "from dotenv import load_dotenv; from runpy import run_path; load_dotenv('.env'); run_path('scripts/smoke_recovery.py', run_name='__main__')" --recording artifacts/replays/worker-crash-recovery.json
backend/.venv/Scripts/python.exe -c "from dotenv import load_dotenv; from runpy import run_path; load_dotenv('.env'); run_path('scripts/smoke_restarts.py', run_name='__main__')" --recording artifacts/replays/component-restarts.json
```

Effect tests use the explicit dedicated `*_test` database. Smoke scripts deliberately
stop/restart development services and restore them in cleanup. These checks do not
establish resilience to destroyed storage or exactly-once external effects.

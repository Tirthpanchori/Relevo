# Testing and verification

Relevo checks durable behavior with real PostgreSQL and process/network failures.
The static website verifies that Replay and Results agree with retained evidence.
Tests are reproducible project checks, not a certification of every deployment.

## Backend

From the repository root with Docker running:

```bash
python scripts/configure.py
docker compose --profile test run --build --rm tests
```

The test profile uses a separate ephemeral PostgreSQL instance, not the
development database. The suite covers submission/idempotency, transaction
rollback, competing claims, ownership across lock waits and expiry, bounded
recovery, retry limits, worker execution, TCP faults, effect protection,
migrations and telemetry. Never point the suite at valuable data.

For Python development with uv:

```bash
uv sync --project backend --locked
uv run --project backend --no-sync ruff check backend scripts
uv run --project backend --no-sync ruff format --check backend scripts
```

Process smoke scripts in `scripts/smoke_worker.py`, `smoke_recovery.py` and
`smoke_restarts.py` exercise local Compose. They intentionally interrupt services;
read their options and use a disposable development environment. The
[recording guide](../artifacts/replays/README.md) provides reproduction commands.

## Frontend

With Node.js 24, from `frontend`:

```bash
npm ci
npm run build
npm test
npx playwright install chromium
npm run test:e2e
```

Linux CI uses `npx playwright install --with-deps chromium`. Windows browser
configuration uses installed Chrome; the tests run serially. The Windows
`scripts/frontend.ps1` wrapper can prepare a project-local Node runtime.

Artifact tests validate recorded events/provenance, reproduce chart summaries
from raw measurements, inspect built routes and scan public files for the local
private token. Browser tests cover navigation, model stages and reverse scroll,
pixels, Flow, Replay, Results, errors, FAQ transitions, keyboard access, Docs
scroll tracking, reduced motion and responsive layouts.

## CI and retained results

GitHub Actions installs locked dependencies and checks fresh source. The backend
workflow runs lint, formatting, PostgreSQL/TCP-fault tests and isolated restore;
the frontend workflow builds and runs artifact, browser and accessibility checks.

Release checkpoint `0d4e5ac24b64d9a9f0a5db678f113767f1d30ea3` passed both
[backend CI](https://github.com/Tirthpanchori/Relevo/actions/runs/41231401626) and
[frontend CI](https://github.com/Tirthpanchori/Relevo/actions/runs/41231401613).
For current status, use [Actions](https://github.com/Tirthpanchori/Relevo/actions).

| Check | Recorded release result |
|---|---|
| Backend suite | 197 passed; 84% coverage |
| Python lint/format | Passed for 79 files |
| Frontend artifact checks | 4 passed |
| Chromium browser tests | 23 passed; no failures/flaky results |
| Automated axe scans | 21 scans; zero violations |
| Restore drill | Schema and full jobs/attempts/events rows match |
| Clean checkout | Startup, fresh credentials, CLI/restarts and 197 tests passed |

Raw dated verification is retained in [`artifacts/verification`](../artifacts/verification).
The original [failure recordings](../artifacts/replays/README.md) and
[benchmark data](../benchmarks/README.md) have their own provenance and limits.
Generated CI reports belong to workflow artifacts; these committed snapshots
are historical evidence, not counters that update on every run.

The browser matrix includes 320–1920px widths, short landscape and reduced
motion. Real iOS/Android devices and Safari/Firefox were not certified. Local
PostgreSQL checks do not certify provider TLS, privileges, cloud durability or
public availability. Secret/advisory scans are bounded checks, not proof against
every security issue. See [security](../SECURITY.md) and
[deployment verification](deployment.md).

# Relevo

**A durable task execution engine.** An application saves background work;
independent workers execute it, and PostgreSQL tracks ownership, attempts and
recovery. Relevo is a backend engineering portfolio project, not a multi-tenant
hosted task service or a promise of exactly-once execution.

## Release status

Deployment preparation is complete on `release/deployment-readiness`; see [release PR #1](https://github.com/Tirthpanchori/Relevo/pull/1).
The current website uses the approved forest/cream/lime design, sticky translucent
navigation, active hero pixels, and six pages. The hero report card is removed.
Desktop/tablet/phone Chromium checks and the independent UI review passed. See the current
audit and exact verification results in [RELEASE-READINESS.md](RELEASE-READINESS.md).
Earlier tests and recordings remain dated evidence; they do not prove a cloud
deployment. No resources have been provisioned and no release has been deployed.

**Deploy it yourself:** [DEPLOYMENT.md](DEPLOYMENT.md) covers Vercel, backend
services, Supabase connections, secrets, migrations, smoke checks and rollback.
The frontend target is Vercel at origin root. A continuously running INR0 backend
on Render/Supabase is not established: sleeping web instances and paid workers
must not be described as free continuous recovery.

## Running and testing

Requirements: Git, Docker Desktop with Linux containers, and Python for the
standard-library setup scripts. Backend development uses Python3.13; Compose
provides the pinned Python/PostgreSQL runtime without a machine-wide upgrade.
Never replace existing `.env` credentials to fix Docker startup.

```powershell
python scripts/configure.py
docker compose up --build -d --wait --wait-timeout 60
docker compose exec -T api python -m relevo --api-url http://127.0.0.1:8000 demo --key my-first-task
```

API: [localhost:8000/docs](http://127.0.0.1:8000/docs). Readiness:
[/health/ready](http://127.0.0.1:8000/health/ready). PostgreSQL is bound to localhost
55432 and persists in a named volume. `docker compose stop` preserves data.
Never run `down -v` against development or production as routine cleanup.

```powershell
docker compose --profile test run --build --rm tests
python scripts/backup_database.py restore-drill
python scripts/backup_database.py backup --output backups/relevo-YYYYMMDD.dump
```

Tests use a separate ephemeral database on55433. The restore drill requires its
migrated schema, creates only uniquely named disposable databases, compares full
rows and drops those databases. Keep backups private and outside the Docker disk.

For local Python development: install uv, then `uv sync --project backend --locked`.
Run `uv run --project backend ruff check backend scripts` and
`uv run --project backend ruff format --check backend scripts`. Docker tests
exercise real PostgreSQL, concurrency and controlled TCP faults.

### Frontend

Windows uses the existing project-local Node24 runtime through the wrapper:

```powershell
./scripts/frontend.ps1 dev
./scripts/frontend.ps1 build
./scripts/frontend.ps1 preview
./scripts/frontend.ps1 test
./scripts/frontend.ps1 test:desktop
```

Development: http://127.0.0.1:5173/ . Production preview: http://127.0.0.1:4173/ .
With Node24 on PATH, run from `frontend`: `npm ci`,
`npx playwright install chromium`, `npm run build`, `npm test`,
`npm run test:e2e`. The last command includes desktop and responsive checks.
Linux browser testing needs `npx playwright install --with-deps chromium`.
Run browser jobs serially on memory-limited machines.

The build creates six HTML directories and404, self-hosted fonts, allowlisted
sanitized evidence, source docs, `llms.txt` and sitemap. Generated files are
ignored. Configure `RELEVO_SITE_URL` or Vercel's production-origin variable for
canonical URLs. No backend secret belongs in frontend environment variables.

## Behavior and boundaries

- Submissions are acknowledged after commit; matching idempotency keys deduplicate.
- Short PostgreSQL transactions claim eligible jobs; handlers run outside locks.
- Renewable leases, worker identity and fencing tokens protect current updates.
- Expired assignments can retry within the saved budget. Retry restarts a handler.
- Heartbeats do not remove the execution deadline or make recovery instantaneous.
- Attempts and transition events remain recorded; terminal outcomes are immutable.
- External effects can repeat and need their own idempotency protection.
- Durable storage is required. Storage destruction, unlimited retries, guaranteed
  uptime and universal benchmark speedups are not promised.

The public site is independent of engine uptime. Flow is illustrative; Replay
uses actual sanitized tests with interventions distinguished from committed
events. Results preserve1,440 recorded measured jobs and their limitations.
Report generation is an example integration, not a built-in handler. Actual
handlers hash payloads, wait, or fail a configured number of attempts.

The shared bearer token is trusted-cluster access, not user tenancy. Keep API
access private to trusted clients, metrics/database ports private, and registered
handlers trusted. The worker is not an arbitrary-code sandbox. See
[security scope](SECURITY.md) and [working guide](working.md).

## Source map

| Location | Purpose |
|---|---|
| `backend/src/relevo` | API, durable engine, migrations, worker, scheduler, client |
| `backend/tests` | Unit, PostgreSQL, race, TCP-fault and effect tests |
| `frontend/src` | Six React/JavaScript pages, original model, evidence readers |
| `frontend/tests` | Browser, responsive, accessibility and artifact checks |
| `scripts` | Credentials, fault smokes, backups, release checks and local tooling |
| `deploy` | Private backend environment template and Supabase privilege script |
| `artifacts/replays`, `benchmarks` | Original recordings/raw measurements and methodology |
| `artifacts/verification` | Dated verification evidence, not live status |

Project records: [plan](implementation-plan.md), [decisions](decision.md),
[working guide](working.md), [design](design.md), [memory](PROJECT_MEMORY.md).
Historical design explorations and previous source snapshots remain local archive
material, excluded from the production bundle; current source is the release authority.
The MIT Anatomy projection kit has [provenance](frontend/src/anatomy/NOTICE.md).
Font licences are copied into the built site. Research screenshots are not shipped.

## CI and handoff

Backend CI installs locked dependencies, lints, tests with real PostgreSQL/TCP
faults and runs the restore drill. Frontend CI installs its lockfile, builds at
root, verifies evidence and runs desktop/tablet/phone browser checks. Release
verification must refer to the exact commit and actual hosted run.

The agent prepares a branch/PR and instructions only. You control account signup,
secrets, merge, resource creation, deployment and the post-deployment smoke checks.
The recurring budget is INR0: paid hosting, paid domains and expiring trials are
outside authorization. See the readiness report for actual remaining blockers.

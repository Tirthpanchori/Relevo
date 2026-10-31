# Release readiness — work in progress

Target: Vercel static site at origin root, private-token backend, user-operated
deployment. Branch: `release/deployment-readiness`. No merge or cloud provisioning.

## Verified so far

- Fresh Linux/PostgreSQL/TCP-fault backend suite:197 passed on the final locked dependencies in26.21s,84% coverage. Ruff lint and formatting passed for79files.
- Actual worker completion, killed-worker recovery/stale update rejection, and
  API/PostgreSQL restarts passed; current captures are in artifacts/verification
  as release-worker-recovery.json and release-component-restarts.json.
- Isolated pg_dump/pg_restore drill restored2synthetic tasks,1attempt,4events and
  the schema marker exactly. No development database was restored or deleted.
- Root-path production build and4evidence/artifact checks passed.
- All23frontend browser cases passed (0failed/flaky);21axe scans found zero violations. Fixes include
  focusable scrolling code blocks and static complete model explanations for
  short landscape viewports. Current viewport targets:320/360/390/768/1024/1440/1920.

## Remaining release gates

- Independent fresh design review: both required agents hit usage limits. Source-derived responsive design records updated; no independent signoff claimed.
- Secret/history scan, clean committed checkout, pushed PR and hosted CI.
- Supabase-specific TLS, privileges and durability checks require the user's
  actual project and are not certified by local PostgreSQL tests.

## Hosting verdict

Vercel root configuration and manual guide are prepared. Full cloud deployment
is unverified. Continuous INR0 Render backend compute is not established; free
web sleep and worker pricing are unresolved budget constraints, not application
test failures. Supabase supplies PostgreSQL, not the Python worker/scheduler.
See [DEPLOYMENT.md](DEPLOYMENT.md). The website remains independent of the engine.

Do not treat this in-progress file or older197-test reports as final release signoff.

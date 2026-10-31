# Release readiness — 1 November 2026

Prepared release: [PR #1](https://github.com/Tirthpanchori/Relevo/pull/1).
No merge, hosting resources or deployment performed.

## Verdicts

| Area | Verdict | Evidence / boundary |
|---|---|---|
| Frontend | Prepared for Vercel deployment | Six responsive pages, root URLs, production build, functional and accessibility checks pass; independent UI review: **ship**. |
| Backend | Prepared for a trusted private deployment | Locked tests, fault/restart smokes, migrations and isolated restore proof pass. Shared token is cluster access, not user tenancy. |
| Hosting | Frontend configured; continuous free backend blocked | Vercel root configuration is prepared. Render Free does not supply always-running worker/scheduler compute. Supabase is PostgreSQL, not Python compute. No provider resources tested. |

## Verification

- **197 backend tests**, including real PostgreSQL, ownership/concurrency and TCP faults; **84% coverage**. Ruff lint and formatting pass for 79 Python files.
- Worker completion, killed-worker recovery/stale-owner rejection, and API/database component restart smoke checks pass. Current sanitized captures: `release-worker-recovery.json` and `release-component-restarts.json`.
- Isolated dump/restore proof: schema marker and complete jobs/attempts/events rows match (2 synthetic jobs, 1 attempt, 4 events). Development storage untouched.
- **23 Chromium browser tests**, zero failures/flaky tests; **21 axe scans**, zero violations. Covers six routes, root utilities and missing-page recovery, widths 320–1920px, short landscape, scroll stages/reversal, Flow/Replay/Results, errors, FAQ reversal, keyboard focus and reduced motion.
- Production build and **4 evidence/artifact tests** pass. Separate clean-clone frontend locked install/build/artifact checks pass.
- Patched committed checkout `9fef03449d311b377750394aeb661adf8d1b0bac` independently passes startup, fresh credentials, CLI before/after restarts, and all 197 tests. Verification-only resources removed; development volume preserved/services restored.
- Current `certifi` is **2026.10.23**, fixing GHSA-6q48-6c7w-9gw2. Exact-version PyPI metadata reports zero active advisories across 53 locked registry packages; npm audit reports zero vulnerabilities.
- Bounded local secret scan: no matching patterns/current credentials in 233 tracked files and 590 reachable history blobs at the patched checkpoint. CI repeats the history-pattern scan. Caches, credentials, dependencies, raw design research and historical source snapshots are excluded from release/build contexts.
- Independent files/capture UI review returned **ship**, with 55 authoritative captures reviewed. Detector ran once with no findings. Source-derived design record refreshed. See `release-design-review.md`; separate remote quality-card comparison was unavailable.

## Hosted CI

Patched application checkpoint `9fef03449d311b377750394aeb661adf8d1b0bac` passed:

- [Backend](https://github.com/Tirthpanchori/Relevo/actions/runs/41231103093)
- [Frontend](https://github.com/Tirthpanchori/Relevo/actions/runs/41231103108)

The final documentation/cleanup commit must also pass both checks before merge;
use the exact current PR head, not these earlier run IDs, for that decision.

## Remaining owner checks

Follow [DEPLOYMENT.md](DEPLOYMENT.md). Configure the canonical HTTPS origin,
credentials, verified database TLS, migration order and Supabase privileges.
After deployment verify direct routes/custom 404/status/headers, private API access,
job completion/recovery, provider persistence, backup/restore and rollback.

No real iOS/Android device, Safari/Firefox, provider TLS/network/privilege,
image/OS-vulnerability or cloud smoke certification is implied. Automated and
pattern checks are bounded evidence, not proof against every security issue.
No exactly-once execution, guaranteed uptime or always-free continuous backend
is claimed. Under INR 0, deploy the website and keep the engine local unless
adequate ongoing free compute is independently available.

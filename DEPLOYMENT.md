# Deploy Relevo yourself

No resources are created by this repository. Merge the reviewed release PR only
after its checks pass. The website uses recorded evidence; it does not need or
receive the engine's token. Cloud smoke tests below are required after you deploy.

## 1. Vercel website (free Hobby, subject to your eligibility)

1. Import `Tirthpanchori/Relevo` in Vercel. Select the reviewed branch for preview;
   use `main` for production after you merge. **Root Directory: repository root**.
2. Keep the checked-in `vercel.json` settings: install `npm ci --prefix frontend`,
   build `npm run build --prefix frontend`, output `frontend/dist`, Node **24.x**.
   Do not use `frontend` as Root Directory: the build reads repository evidence.
3. Enable Vercel system environment variables. Set `RELEVO_SITE_URL` to your
   final HTTPS origin, including a trailing slash (for example
   `https://your-project.vercel.app/`), for the canonical production URL.
   If omitted, `VERCEL_PROJECT_PRODUCTION_URL` supplies the project origin;
   local builds use localhost. Redeploy after changing the canonical origin.
4. Do not set `RELEVO_API_TOKEN`, database credentials or Supabase keys in Vercel.
   No paid domain is needed. The site uses root paths, not `/Relevo/`.
5. Visit `/`, `/engine/#flow`, `/engine/#replay`, `/results/`, `/docs/#api`,
   `/about/`, `/privacy/`, `/llms.txt`, `/sitemap.xml`, and a nonexistent URL.
   Refresh each direct route. Confirm missing URLs show the custom 404, and
   canonical/sitemap URLs use your production origin. Inspect response security
   headers and the browser console. Test on a real phone as well as desktop.
6. Roll back website code using Vercel's previous successful deployment. Keep
   deployment auto-publishing under your account's control; this agent did not
   create a Vercel project or enable an integration.

## 2. Backend hosting gate: Render and Supabase

**A continuously running INR0 Render backend is NOT established.** Render's free
web service sleeps after 15 minutes without inbound traffic. Background workers
require a suitable compute plan; do not select a paid plan under a zero budget.
Render's free PostgreSQL expires after 30 days, so it is not the database target.
Supabase Free can pause for inactivity and does not make compute hosting free.
Do not use artificial keep-alive requests, trial credits, or combine workers into
a sleeping API and describe it as reliable continuous recovery.

If INR0 remains mandatory and no adequate free compute host is available, deploy
only the website; run the engine through local Docker and label hosted backend
as blocked. The following is the **conditional manual configuration**, not a
claim that resources, provider compatibility or free capacity were tested.

## 3. Supabase PostgreSQL, if you choose to provision it

1. Create a dedicated project for this engine. Keep the database password private.
   Relevo does not use Supabase Auth, Storage, REST access or browser SDK keys.
2. Use a **direct PostgreSQL connection**, or the **session pooler on 5432** when
   IPv4 is required. Do not use transaction pooling on 6543: Relevo uses session
   settings and Psycopg prepared statements. Prefer direct access for migrations
   and dumps. Confirm the provider supports the tested durability settings and
   SQL features; local verification targets PostgreSQL 18.
3. Set a server-only `RELEVO_DATABASE_URL`, changing the URI driver prefix to
   `postgresql+psycopg://`. Percent-encode special characters in credentials.
   Use `sslmode=verify-full` and the project's CA certificate path through
   `sslrootcert`, mounted as a provider secret file. Do not disable TLS checks.
4. From the built runtime image with the database URL and token configured, run
   `alembic upgrade head` once before API/worker/scheduler startup. Migrations
   require ownership/create permissions; use a dedicated migration role and
   appropriately restricted runtime roles when configuring production access.
5. Run `deploy/supabase-private.sql` as the migration owner. Disable the Data API
   for the dedicated project if unused. Verify anon/authenticated SDK credentials
   cannot read or mutate engine tables. These cloud privilege checks remain
   mandatory even though the Python API requires a bearer token.
6. Confirm `/health/ready` returns success and exercise authenticated submission,
   deduplication, inspection and worker completion before admitting useful work.
   Never paste server credentials into the website or commit them to Git.

## 4. Render compute, only on an acceptable plan

Build from repository root using `backend/Dockerfile`, runtime target. Services:

| Service | Command | Server-only environment |
|---|---|---|
| API web service | `uvicorn relevo.api.app:create_app --factory --host 0.0.0.0 --port $PORT --no-access-log` | `RELEVO_DATABASE_URL`, `RELEVO_API_TOKEN` |
| Worker background service | `python -m relevo.worker` | `RELEVO_API_URL`, same `RELEVO_API_TOKEN` |
| Recovery background service | `python -m relevo.scheduler` | `RELEVO_DATABASE_URL`, same `RELEVO_API_TOKEN` |

Set Docker commands in the provider interface; shell expansion of `$PORT` must
be enabled for the API command. Health-check path `/health/ready`. Start with one
worker; increase only after measuring memory and DB connections. Keep the default
50ms monitor and compatible lease/heartbeat settings. Each child executes only a
registered trusted handler: this is not an untrusted code sandbox.

Use HTTPS for any public origin. `RELEVO_API_URL` is an origin with no path/query.
Use the private service address when supported. Keep database and metrics ports
private; do not expose Compose's localhost port mappings publicly. Auth protects
metrics and all task/worker operations; the single shared token is trusted-cluster
access, not per-user tenancy or public multi-user authorization. Put network
restrictions and request-rate controls at the hosting boundary before giving
access beyond yourself. There is no browser credential flow or anonymous demo.

Run the migration as a one-off controlled job **before** starting the new version.
For schema changes, back up first and use a maintenance window if compatibility
is uncertain. Never run migrations independently in each API replica. Public
hosting, TLS/certificate mounting, limits and Supabase availability need your
deployed verification; local green CI cannot prove them.

## 5. Backups, restore and rollback

- Local backup: `python scripts/backup_database.py backup --output backups/relevo-YYYYMMDD.dump`.
  Requires development Compose PostgreSQL running; refuses to overwrite a file.
  Dumps contain private task data. Store an encrypted copy outside the Docker disk
  and repository, with restricted access. Do not rely on the development volume
  or an unverified free-provider backup promise.
- Local proof: after the full test suite migrates `postgres-test`, run
  `python scripts/backup_database.py restore-drill`. It creates two unique test
  databases, seeds pending/completed tasks and attempt/event rows in the migrated
  schema, dumps/restores them, compares complete rows and drops only those two
  temporary databases. Development storage is untouched.
- Hosted backup: use PostgreSQL client tools compatible with the server version,
  with credentials via a protected service/password file, not command arguments.
  Run `pg_dump --format=custom --no-owner --file=PRIVATE_BACKUP.dump` against the
  dedicated project. Use a manual pre-release backup and a regular schedule that
  fits free storage/egress limits; Supabase Free needs off-site exports.
- Restore to a **new isolated database/project**, using
  `pg_restore --no-owner --no-privileges --exit-on-error --dbname=NEW_DATABASE PRIVATE_BACKUP.dump`.
  Verify schema head, counts and full sampled task/attempt/event identities,
  authentication and completion before changing the runtime connection. Never
  restore over a running engine or use `--clean` against development/production.
- Roll back application images to the previous tested revision only if they
  support the current schema. Avoid blind migration downgrades; prefer a forward
  fix or tested restore into a new database. Keep the old database until verified.

## 6. Your post-deployment checklist

- Confirm free-plan eligibility/limits and billing settings before creation;
  no paid upgrades or trial credits are part of this release.
- Check HTTPS, canonical URLs, all direct routes and custom 404.
- Check missing/wrong API token rejection, no public DB/metrics access, and no
  token in static assets or logs. Check Supabase Data API restrictions separately.
- Submit one built-in job privately, inspect attempts/result, retry the same
  idempotency key, restart a worker and verify bounded recovery with storage intact.
- Save a backup, restore into an isolated target and verify it before relying on it.
- Record the actual deployment URL/revision and results. Until then cloud readiness
  is conditional and public uptime/always-free capacity is not claimed.

Provider references checked for this release:
[Vercel configuration](https://vercel.com/docs/project-configuration),
[Render free limitations](https://render.com/docs/free),
[Render workers](https://render.com/docs/background-workers),
[Supabase connections](https://supabase.com/docs/guides/database/connecting-to-postgres),
[Supabase backups](https://supabase.com/docs/guides/platform/backups),
[Supabase free pausing](https://supabase.com/docs/guides/platform/free-project-pausing).

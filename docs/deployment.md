# Deployment

The current arrangement is a public static website on Vercel and a private
backend running locally through Docker Compose. The website's recordings and
measurements work when the local backend is stopped. No tunnel or public API
address is required.

## Vercel website

1. Import `Tirthpanchori/Relevo` and use `main` as the production branch after
   reviewed changes are merged.
2. Select the **Other** application preset and **repository root (`./`)**.
   The build reads evidence outside `frontend`, so do not restrict the root to
   that subdirectory or enable the multi-service backend import.
3. Use Node.js **24.x** and the checked-in `vercel.json` settings:

   | Setting | Value |
   |---|---|
   | Install command | `npm ci --prefix frontend` |
   | Build command | `npm run build --prefix frontend` |
   | Output directory | `frontend/dist` |

4. Set the production environment variable
   `RELEVO_SITE_URL=https://relevo-engine.vercel.app/` and redeploy after changing
   the production domain. This controls canonical links, sitemap and site links.
   Without an explicit value, Vercel's production-origin variable is used;
   local builds use localhost.
5. Do not put the API token, database password or Supabase keys into Vercel.
   The frontend does not need them.
6. Check `/`, `/engine/#flow`, `/engine/#replay`, `/results/`, `/docs/`, `/about/`,
   `/privacy/`, `/llms.txt`, `/sitemap.xml` and a nonexistent URL. Refresh direct
   routes; check canonical URLs, custom 404 behavior, console and security headers.

Vercel owns the hosted build/deployment lifecycle. A previous successful
deployment can be promoted for rollback. Verify provider plan eligibility and
limits before enabling paid features; the project does not require a paid domain.

## Local Docker backend

Install Docker with Linux-container support and Python for the setup script.
From the repository root:

```bash
python scripts/configure.py
docker compose up --build -d --wait --wait-timeout 90
docker compose exec -T api python -m relevo --api-url http://127.0.0.1:8000 demo --key deployment-check
```

The setup script generates `.env` credentials once and does not overwrite an
existing file. Compose starts PostgreSQL, applies migrations, then starts the
API, worker and recovery scheduler. Workers communicate with the API; the
scheduler and API use PostgreSQL. Health checks gate startup.

The API binds to localhost port 8000; PostgreSQL binds to localhost port 55432.
Do not open those ports on the public internet or place secrets in command
arguments. Use `docker compose logs api worker scheduler` for local diagnostics
and `/health/ready` for readiness. Do not post private logs or job contents publicly.

The laptop must be awake with Docker running for work and recovery to proceed.
Stopping it delays processing; persistent database state is stored in a named
Docker volume. Resume with the same Compose configuration and volume.

## Backups and stopping safely

```bash
docker compose stop
docker compose up -d --wait --wait-timeout 90
```

Stopping preserves the database. Never use `docker compose down -v` as routine
cleanup: it removes the named volume and can destroy saved work.

With development PostgreSQL running, create a private backup:

```bash
python scripts/backup_database.py backup --output backups/relevo-YYYYMMDD.dump
```

The command refuses to overwrite an existing file. Dumps contain private task
data: keep an encrypted copy outside the Docker disk and repository. A volume
alone is not an independent backup.

To reproduce the isolated restore proof:

```bash
docker compose --profile test run --build --rm tests
python scripts/backup_database.py restore-drill
```

The drill seeds a migrated test schema in uniquely named temporary databases,
dumps/restores it, compares complete rows and drops only those databases.
Development storage is untouched. It proves the procedure with synthetic
fixtures; verify a real backup in a new isolated target before relying on it.
Never restore over a running engine. For a schema-changing upgrade, back up
first and prefer a compatible application rollback or tested forward fix over
an untested migration downgrade.

## Optional hosted backend

Hosting the engine requires compute for the API, workers and recovery scheduler,
plus durable PostgreSQL. Supabase can supply the database; it does not run these
Python processes. Render Free web services sleep when idle and its free service
types exclude background workers. That is not continuous free recovery hosting.

The retained `deploy` templates describe a possible private deployment; they
are not proof of a running or free-compatible cloud backend. Use direct or
session-pooled PostgreSQL rather than transaction pooling, verified TLS,
private server credentials, one controlled migration before runtime startup,
and separate Supabase Data API privilege checks. Public backend hosting needs
its own tested startup, persistence, rate controls, backups and rollback plan.

References: [Vercel configuration](https://vercel.com/docs/project-configuration),
[Render free limits](https://render.com/docs/free),
[Supabase connections](https://supabase.com/docs/guides/database/connecting-to-postgres).

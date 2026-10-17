# Backend measurement method

The benchmark script uses the separate `benchmark` Compose profile and refuses
any database other than `127.0.0.1:15434/relevo_benchmark`. It truncates that
database between cases. Development/test databases are untouched. Normal
PostgreSQL `fsync`, `synchronous_commit`, and `full_page_writes` must stay on.

Each case runs ten warmup hashing jobs, then admits a fixed backlog of thirty
jobs before a shared database-time eligibility gate. There are three repetitions
at each of 1, 3, and 5 workers. Both variants use identical workloads: canonical
hashing of `{"message": "x" * 1024}` and a 0.25-second timed handler. The timed
handler sleeps; it represents waiting work, not CPU-intensive computation.
Submission concurrency is eight. Throughput is jobs divided by database-measured
eligibility-to-last-terminal time. Queue delay excludes intentional scheduling.
Attempt duration includes process startup, execution, supervision, and reporting.
The script validates every acknowledged ID, exact result, single attempt/token,
and ordered submitted/claimed/succeeded history before retaining a case.

Raw JSON includes per-job timings, inclusive interpolated p50/p95/p99 client
request latency (submission and ten post-run inspections), API/worker histogram
deltas, sampled container CPU/resident memory, PostgreSQL lock-wait/active
connection samples, dependency/lock versions, durability settings, source hash,
Git revision, image ID, and Docker/host resources. Docker CPU is percent of one
core; container memory includes children. Samples miss brief peaks. PostgreSQL
lock samples every 50 ms can miss brief contention. Histogram percentiles are
bucket approximations, separate from exact client measurements. The observer and
Docker Desktop add overhead; these are local finite-backlog results, not capacity
or uptime guarantees. HTTP submission latency includes admission before the gate.

Search budget: at most two single-hypothesis candidates, 30 minutes of measurement,
INR 0 spend, and writes only to the dedicated benchmark database. First retain a
baseline, identify a measured bottleneck, then compare identical cases. Promote
only a repeated improvement with full correctness tests and an obvious rollback.
Confirm with another baseline/winner comparison. No default has been changed yet.

From the root, after a committed source checkpoint and locked dependency install:

```powershell
docker compose --profile benchmark up --build -d --wait --wait-timeout 90 postgres-benchmark benchmark-migrate benchmark-api benchmark-scheduler
.tools/Scripts/uv.exe run --project backend --env-file .env --no-sync python scripts/benchmark.py --variant baseline --monitor 0.05 --output benchmarks/raw/baseline.json
```

The script stops benchmark services on exit and preserves the named benchmark
volume. Start the profile services again before another matrix. Exporters and
monitoring scrapes are off in the benchmark profile; telemetry collection stays
enabled. Results and any promoted change will be documented after measurement.

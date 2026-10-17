# Local backend benchmark comparison

Source: `b84be4e24b46458b22382ddb2c7be07392a1f293`. Same runtime image and workload; only the worker monitor interval changes.

Baseline: 0.05 seconds. Candidate: 0.005 seconds.

Host: Intel64 Family 6 Model 154 Stepping 3, GenuineIntel; Windows-11-10.0.26340-SP0. Docker: 16 logical CPUs, 7.57 GiB RAM, 6.6.87.2-microsoft-standard-WSL2.

All retained cases validated acknowledged IDs, exact results, single attempts/tokens, and complete ordered history. Durability stays on. Figures below are medians across 1 case(s) per group; ranges show throughput variation.

| Workload | Workers | Baseline jobs/s (range) | Candidate jobs/s (range) | Change | Queue p95 ms baseline → candidate | Submit p95 ms baseline → candidate |
|---|---:|---:|---:|---:|---:|---:|
| short_hash | 1 | 3.103 (3.103–3.103) | 4.001 (4.001–4.001) | +28.9% | 8906.5 → 6948.9 | 97.2 → 106.6 |
| short_hash | 3 | 7.303 (7.303–7.303) | 8.940 (8.940–8.940) | +22.4% | 3703.6 → 3044.5 | 168.2 → 146.2 |
| short_hash | 5 | 10.580 (10.580–10.580) | 10.621 (10.621–10.621) | +0.4% | 2367.5 → 2413.8 | 118.5 → 119.7 |
| long_timed | 1 | 1.760 (1.760–1.760) | 1.626 (1.626–1.626) | -7.6% | 15808.3 → 16876.0 | 168.7 → 159.6 |
| long_timed | 3 | 5.007 (5.007–5.007) | 4.878 (4.878–4.878) | -2.6% | 5157.3 → 5580.1 | 121.0 → 112.9 |
| long_timed | 5 | 7.566 (7.566–7.566) | 5.796 (5.796–5.796) | -23.4% | 3279.5 → 4137.3 | 109.0 → 145.1 |

| Variant | Workload | Workers | Child mean ms | Supervision mean ms | Worker CPU % | API CPU % | PostgreSQL CPU % | Max sampled worker MiB | Lock-wait sample max |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| baseline | short_hash | 1 | 0.079 | 261.28 | 56.7 | 16.0 | 8.4 | 69.2 | 0 |
| candidate | short_hash | 1 | 0.096 | 221.23 | 62.4 | 21.6 | 5.8 | 68.8 | 0 |
| baseline | short_hash | 3 | 0.108 | 358.22 | 132.7 | 26.1 | 11.3 | 73.0 | 0 |
| candidate | short_hash | 3 | 0.088 | 280.73 | 106.0 | 19.2 | 8.2 | 72.9 | 0 |
| baseline | short_hash | 5 | 0.130 | 385.04 | 151.6 | 23.5 | 10.6 | 72.9 | 0 |
| candidate | short_hash | 5 | 0.121 | 384.51 | 158.7 | 33.2 | 10.7 | 72.5 | 0 |
| baseline | long_timed | 1 | 250.232 | 511.12 | 41.9 | 17.5 | 5.7 | 75.7 | 0 |
| candidate | long_timed | 1 | 250.182 | 570.14 | 55.5 | 20.2 | 7.0 | 75.4 | 0 |
| baseline | long_timed | 3 | 250.204 | 536.44 | 96.6 | 17.4 | 6.0 | 75.2 | 0 |
| candidate | long_timed | 3 | 250.173 | 562.11 | 121.6 | 26.0 | 8.2 | 75.6 | 0 |
| baseline | long_timed | 5 | 250.162 | 584.35 | 140.0 | 21.5 | 7.0 | 75.1 | 0 |
| candidate | long_timed | 5 | 258.888 | 658.28 | 194.3 | 29.2 | 12.2 | 75.4 | 0 |

CPU figures sum the per-container sample means for each role; 100% is one core. Memory is the largest observed individual worker container, including children, not an aggregate or true peak. Resource sampling includes gate/admission time. Lock samples can miss brief waits. Raw data includes all API, scheduler, worker, and database samples and API histograms.

Raw baseline: [confirmation-awake-50ms.json](raw/confirmation-awake-50ms.json); candidate: [confirmation-awake-5ms.json](raw/confirmation-awake-5ms.json). [Method and commands](README.md). Results describe local fixed-backlog runs under Docker Desktop, not a service capacity or scaling guarantee. The timed workload waits rather than performs CPU-intensive computation.

Promotion/confirmation status is recorded separately in the implementation plan and decision log.

These paired runs used the same `b84be4e` runtime image. A later audit found that
its server logging setup inadvertently re-enabled access logging despite the CLI
flag; that behavior was corrected after these measurements. Both paired variants
shared the issue. These remain measurements of the recorded revision, not a
capacity claim for later revisions.

The decision remains conservative: keep the 50 ms default. The 5 ms setting is an
optional short-task tuning mode with validated correctness and explicit measured
regressions for timed work. One confirmation case per group is descriptive;
consult the earlier three-repeat matrix and raw measurements as well.

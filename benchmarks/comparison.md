# Local backend benchmark comparison

Source: `957e0075356de0bf5d49cccb21c45ab67b2372b0`. Same runtime image and workload; only the worker monitor interval changes.

Baseline: 0.05 seconds. Candidate: 0.005 seconds.

Host: Intel64 Family 6 Model 154 Stepping 3, GenuineIntel; Windows-11-10.0.26340-SP0. Docker: 16 logical CPUs, 7.57 GiB RAM, 6.6.87.2-microsoft-standard-WSL2.

All retained cases validated acknowledged IDs, exact results, single attempts/tokens, and complete ordered history. Durability stays on. Figures below are medians across 3 case(s) per group; ranges show throughput variation.

| Workload | Workers | Baseline jobs/s (range) | Candidate jobs/s (range) | Change | Queue p95 ms baseline → candidate | Submit p95 ms baseline → candidate |
|---|---:|---:|---:|---:|---:|---:|
| short_hash | 1 | 3.383 (3.064–3.780) | 4.204 (3.389–4.213) | +24.2% | 8049.7 → 6611.1 | 171.4 → 131.6 |
| short_hash | 3 | 7.072 (6.958–7.921) | 7.369 (5.638–7.738) | +4.2% | 3704.7 → 3502.2 | 166.1 → 123.1 |
| short_hash | 5 | 8.937 (8.324–10.573) | 12.430 (11.769–12.474) | +39.1% | 2729.6 → 1987.4 | 149.7 → 117.8 |
| long_timed | 1 | 1.834 (1.713–1.898) | 1.954 (1.951–2.019) | +6.6% | 15146.8 → 14039.1 | 125.2 → 121.1 |
| long_timed | 3 | 4.863 (4.526–5.113) | 4.984 (4.753–5.162) | +2.5% | 5501.1 → 5013.9 | 128.1 → 126.0 |
| long_timed | 5 | 7.186 (6.560–7.601) | 6.918 (6.654–7.139) | -3.7% | 3467.8 → 3490.2 | 147.2 → 126.3 |

| Variant | Workload | Workers | Child mean ms | Supervision mean ms | Worker CPU % | API CPU % | PostgreSQL CPU % | Max sampled worker MiB | Lock-wait sample max |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| baseline | short_hash | 1 | 0.092 | 266.37 | 59.0 | 16.0 | 7.2 | 73.2 | 0 |
| candidate | short_hash | 1 | 0.082 | 211.45 | 57.3 | 16.0 | 5.5 | 73.5 | 0 |
| baseline | short_hash | 3 | 0.113 | 362.93 | 117.0 | 25.1 | 8.3 | 71.7 | 0 |
| candidate | short_hash | 3 | 0.107 | 345.57 | 144.1 | 28.7 | 8.1 | 72.5 | 0 |
| baseline | short_hash | 5 | 0.128 | 468.47 | 180.6 | 19.7 | 11.0 | 72.9 | 0 |
| candidate | short_hash | 5 | 0.109 | 338.17 | 127.7 | 19.4 | 7.1 | 73.1 | 0 |
| baseline | long_timed | 1 | 250.233 | 516.52 | 43.9 | 17.0 | 7.1 | 75.7 | 0 |
| candidate | long_timed | 1 | 250.220 | 470.45 | 45.7 | 14.6 | 6.3 | 75.8 | 0 |
| baseline | long_timed | 3 | 250.179 | 562.37 | 98.9 | 24.1 | 8.6 | 76.9 | 0 |
| candidate | long_timed | 3 | 250.197 | 540.83 | 110.9 | 19.5 | 6.3 | 75.6 | 0 |
| baseline | long_timed | 5 | 250.219 | 617.27 | 167.1 | 25.2 | 8.8 | 75.4 | 0 |
| candidate | long_timed | 5 | 250.190 | 624.82 | 170.6 | 23.6 | 8.3 | 75.4 | 0 |

CPU figures sum the per-container sample means for each role; 100% is one core. Memory is the largest observed individual worker container, including children, not an aggregate or true peak. Resource sampling includes gate/admission time. Lock samples can miss brief waits. Raw data includes all API, scheduler, worker, and database samples and API histograms.

Raw baseline: [baseline-complete.json](raw/baseline-complete.json); candidate: [monitor-5ms.json](raw/monitor-5ms.json). [Method and commands](README.md). Results describe local fixed-backlog runs under Docker Desktop, not a service capacity or scaling guarantee. The timed workload waits rather than performs CPU-intensive computation.

Promotion/confirmation status is recorded separately in the implementation plan and decision log.

The repeated baseline spans two sessions; resume metadata verifies unchanged
runtime source, image, workload, and configuration. During the first repetition of
the 5 ms candidate, a targeted native logging audit also ran on this shared PC.
Desktop background activity, caches, and scheduling were not fully isolated.
Those cases remain visible rather than being removed selectively.

The largest observed deltas exceed what the 45 ms reduction in maximum polling
delay alone explains. They must not be presented as a guaranteed speedup caused
only by the interval change. The timed five-worker workload also regressed 3.7%
in the repeated matrix, within overlapping run ranges. Use the separately recorded
confirmation on one updated runtime image, after correctness checks have finished,
to decide whether to promote the setting. The legacy repeated comparison remains
useful evidence of actual measurements and their variation.

The subsequent confirmation has its own [revision-specific notes](confirmation-notes.md).

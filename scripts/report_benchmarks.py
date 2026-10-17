"""Recompute a readable comparison and job CSV from retained benchmark measurements."""

import argparse
import csv
import json
import statistics
from pathlib import Path


def median(runs, key):
    return statistics.median(key(run) for run in runs)


def duration(run, name):
    values = {row["name"]: row["value"] for row in run["worker_histogram_delta"]}
    return values[f"{name}_sum"] / values[f"{name}_count"]


def memory_mib(value):
    number, unit = (
        value.split(" / ")[0].split(maxsplit=1)
        if " " in value.split(" / ")[0]
        else (None, None)
    )
    if number is None:
        import re

        number, unit = re.fullmatch(
            r"([0-9.]+)([A-Za-z]+)", value.split(" / ")[0]
        ).groups()
    multipliers = {
        "B": 1 / 1048576,
        "KiB": 1 / 1024,
        "MiB": 1,
        "GiB": 1024,
        "kB": 1000 / 1048576,
        "MB": 1000000 / 1048576,
        "GB": 1000000000 / 1048576,
    }
    return float(number) * multipliers[unit]


def resources(run, role):
    by_container = {}
    for row in run["container_samples"]:
        if role in row["Name"]:
            by_container.setdefault(row["Name"], []).append(row)
    assert by_container, "Missing resource observations"
    cpu = sum(
        statistics.mean(float(row["CPUPerc"].rstrip("%")) for row in rows)
        for rows in by_container.values()
    )
    memory = max(
        memory_mib(row["MemUsage"]) for rows in by_container.values() for row in rows
    )
    return cpu, memory


def main(baseline_path, candidate_path, output):
    base, candidate = [
        json.loads(path.read_text(encoding="utf-8"))
        for path in (baseline_path, candidate_path)
    ]
    assert (
        base["configuration"]
        | {"monitor_seconds": candidate["configuration"]["monitor_seconds"]}
        == candidate["configuration"]
    )
    assert (
        base["revision"]["runtime_source_sha256"]
        == candidate["revision"]["runtime_source_sha256"]
    )
    assert base["revision"]["image_id"] == candidate["revision"]["image_id"]
    assert len(base["runs"]) == len(candidate["runs"])
    lines = [
        "# Local backend benchmark comparison",
        "",
        f"Source: `{base['revision']['git_commit']}`. Same runtime image and workload; only the worker monitor interval changes.",
        "",
        f"Baseline: {base['configuration']['monitor_seconds']} seconds. Candidate: {candidate['configuration']['monitor_seconds']} seconds.",
        "",
        f"Host: {base['host']['processor']}; {base['host']['platform']}. Docker: {base['host']['docker']['cpus']} logical CPUs, {base['host']['docker']['memory_bytes'] / 2**30:.2f} GiB RAM, {base['host']['docker']['kernel']}.",
        "",
        "All retained cases validated acknowledged IDs, exact results, single attempts/tokens, and complete ordered history. Durability stays on. Figures below are medians across repeated cases; ranges show throughput variation.",
        "",
        "| Workload | Workers | Baseline jobs/s (range) | Candidate jobs/s (range) | Change | Queue p95 ms baseline → candidate | Submit p95 ms baseline → candidate |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    groups = []
    for workload in ("short_hash", "long_timed"):
        for workers in (1, 3, 5):
            a, b = [
                [
                    run
                    for run in data["runs"]
                    if run["workload"] == workload and run["workers"] == workers
                ]
                for data in (base, candidate)
            ]
            assert a and len(a) == len(b) == base["configuration"]["repeats"]
            groups.append((workload, workers, a, b))
            rates = [
                [run["throughput_jobs_per_second"] for run in group] for group in (a, b)
            ]
            medians = [statistics.median(values) for values in rates]
            queue = [
                median(group, lambda run: run["queue_seconds"]["p95"]) * 1000
                for group in (a, b)
            ]
            submit = [
                median(group, lambda run: run["submission_seconds"]["p95"]) * 1000
                for group in (a, b)
            ]
            lines.append(
                f"| {workload} | {workers} | {medians[0]:.3f} ({min(rates[0]):.3f}–{max(rates[0]):.3f}) | {medians[1]:.3f} ({min(rates[1]):.3f}–{max(rates[1]):.3f}) | {(medians[1] / medians[0] - 1) * 100:+.1f}% | {queue[0]:.1f} → {queue[1]:.1f} | {submit[0]:.1f} → {submit[1]:.1f} |"
            )
    lines += [
        "",
        "| Variant | Workload | Workers | Child mean ms | Supervision mean ms | Worker CPU % | API CPU % | PostgreSQL CPU % | Max sampled worker MiB | Lock-wait sample max |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for workload, workers, a, b in groups:
        for label, group in (("baseline", a), ("candidate", b)):
            body = (
                median(
                    group, lambda run: duration(run, "relevo_worker_execution_seconds")
                )
                * 1000
            )
            supervision = (
                median(
                    group,
                    lambda run: duration(run, "relevo_worker_supervision_seconds"),
                )
                * 1000
            )
            worker_cpu = median(
                group, lambda run: resources(run, "benchmark-worker")[0]
            )
            api_cpu = median(group, lambda run: resources(run, "benchmark-api")[0])
            db_cpu = median(group, lambda run: resources(run, "postgres-benchmark")[0])
            mem = max(resources(run, "benchmark-worker")[1] for run in group)
            lock = max(
                row["lock_waiters"] for run in group for row in run["database_samples"]
            )
            lines.append(
                f"| {label} | {workload} | {workers} | {body:.3f} | {supervision:.2f} | {worker_cpu:.1f} | {api_cpu:.1f} | {db_cpu:.1f} | {mem:.1f} | {lock} |"
            )
    lines += [
        "",
        "CPU figures sum the per-container sample means for each role; 100% is one core. Memory is the largest observed individual worker container, including children, not an aggregate or true peak. Resource sampling includes gate/admission time. Lock samples can miss brief waits. Raw data includes all API, scheduler, worker, and database samples and API histograms.",
        "",
        f"Raw baseline: [{baseline_path.name}](raw/{baseline_path.name}); candidate: [{candidate_path.name}](raw/{candidate_path.name}). [Method and commands](README.md). Results describe local fixed-backlog runs under Docker Desktop, not a service capacity or scaling guarantee. The timed workload waits rather than performs CPU-intensive computation.",
        "",
        "Promotion/confirmation status is recorded separately in the implementation plan and decision log.",
        "",
    ]
    output.write_text("\n".join(lines), encoding="utf-8")
    with output.with_suffix(".csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(
            stream,
            fieldnames=[
                "variant",
                "workload",
                "workers",
                "repeat",
                "job_id",
                "worker_id",
                "created_at",
                "started_at",
                "finished_at",
                "queue_seconds",
                "attempt_seconds",
                "eligible_to_terminal_seconds",
            ],
        )
        writer.writeheader()
        for label, data in (("baseline", base), ("candidate", candidate)):
            for run in data["runs"]:
                for job in run["jobs"]:
                    writer.writerow(
                        {
                            "variant": label,
                            "workload": run["workload"],
                            "workers": run["workers"],
                            "repeat": run["repeat"],
                            **job,
                        }
                    )
    print(f"Recomputed comparison: {output}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("baseline", type=Path)
    parser.add_argument("candidate", type=Path)
    parser.add_argument("--output", type=Path, default=Path("benchmarks/comparison.md"))
    args = parser.parse_args()
    main(args.baseline, args.candidate, args.output)

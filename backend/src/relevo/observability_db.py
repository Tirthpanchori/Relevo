"""Read-only durable metrics; never substitute a process counter for committed history."""

from prometheus_client.core import CounterMetricFamily, GaugeMetricFamily, HistogramMetricFamily
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from relevo.observability import BUCKETS


class DurableCollector:
    def __init__(self, engine):
        self.engine = engine

    def describe(self):
        return []

    def collect(self):
        try:
            with self.engine.connect().execution_options(
                isolation_level="REPEATABLE READ"
            ) as connection:
                connection.execute(text("SET TRANSACTION READ ONLY"))
                states = connection.execute(
                    text("SELECT state, count(*) FROM jobs GROUP BY state")
                ).all()
                transitions = connection.execute(
                    text("""
                    SELECT kind, count(*) AS total,
                        count(*) FILTER (WHERE data->>'retry_scheduled'='true') AS retries
                    FROM job_events GROUP BY kind
                """)
                ).all()
                histograms = []
                for field, name, description in (
                    (
                        "queue_delay_seconds",
                        "relevo_durable_queue_delay_seconds",
                        "Committed eligible-to-claim delay",
                    ),
                    (
                        "attempt_duration_seconds",
                        "relevo_durable_attempt_duration_seconds",
                        "Claim-to-outcome or expiry duration",
                    ),
                ):
                    counts = ", ".join(
                        f"count(*) FILTER (WHERE value <= {bound})" for bound in BUCKETS
                    )
                    row = connection.execute(
                        text(f"""
                        SELECT count(*), coalesce(sum(value),0), {counts}
                        FROM (SELECT (data->>'{field}')::double precision AS value
                              FROM job_events
                              WHERE jsonb_typeof(data->'{field}')='number') AS metric_values
                    """)
                    ).one()
                    histogram = HistogramMetricFamily(name, description)
                    buckets = [(str(bound), row[index + 2]) for index, bound in enumerate(BUCKETS)]
                    buckets.append(("+Inf", row[0]))
                    histogram.add_metric([], buckets=buckets, sum_value=row[1])
                    histograms.append(histogram)
            gauge = GaugeMetricFamily("relevo_jobs", "Current durable job states", labels=["state"])
            counts = dict(states)
            for state in ("pending", "running", "succeeded", "failed"):
                gauge.add_metric([state], counts.get(state, 0))
            counter = CounterMetricFamily(
                "relevo_durable_transitions_total", "Committed state transitions", labels=["kind"]
            )
            retries = 0
            for kind, total, retry_count in transitions:
                counter.add_metric(
                    [
                        kind
                        if kind in {"submitted", "claimed", "succeeded", "failed", "expired"}
                        else "other"
                    ],
                    total,
                )
                retries += retry_count
            yield gauge
            yield counter
            yield CounterMetricFamily(
                "relevo_durable_retries_total", "Committed retry scheduling", value=retries
            )
            yield from histograms
            yield GaugeMetricFamily(
                "relevo_database_metrics_up", "Durable metrics query succeeded", value=1
            )
        except SQLAlchemyError:
            # Missing values signal unavailable data; emitting zero would falsely imply lost work.
            yield GaugeMetricFamily(
                "relevo_database_metrics_up", "Durable metrics query succeeded", value=0
            )

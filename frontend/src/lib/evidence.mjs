export const eventLabels = {
  submitted: 'Job saved', claimed: 'Assignment claimed', expired: 'Lease expired',
  succeeded: 'Outcome committed', failed: 'Attempt failed',
};

export function validateCapture(capture) {
  if (!capture || !Array.isArray(capture.events) || !Array.isArray(capture.attempts) || !capture.source?.path || !capture.revision?.git_commit) {
    throw new Error('The recording is missing its event history or provenance.');
  }
  if (!capture.events.length || capture.events.some((event, index) => event.sequence !== index + 1 || !Number.isFinite(Date.parse(event.occurred_at)))) {
    throw new Error('The recording has an invalid ordered event history.');
  }
  return capture;
}

export function replayFrame(capture, index) {
  validateCapture(capture);
  const event = capture.events[Math.max(0, Math.min(index, capture.events.length - 1))];
  const attempt = capture.attempts.find(item => item.id === event.attempt_id);
  const elapsed = (Date.parse(event.occurred_at) - Date.parse(capture.events[0].occurred_at)) / 1000;
  return {
    event, attempt, elapsed,
    state: event.data.state,
    label: eventLabels[event.kind] || event.kind,
    component: event.kind === 'submitted' ? 'database' : event.kind === 'expired' ? 'scheduler' : event.kind === 'claimed' ? 'workers' : 'coordinator',
  };
}

export function eventExplanation(event) {
  if (event.kind === 'submitted') return 'The submission and its pending state were committed to PostgreSQL. Acknowledgment follows the commit.';
  if (event.kind === 'claimed') return `An eligible assignment was claimed with fencing token ${event.data.fencing_token}. The job is running; the task executes outside the claim transaction.`;
  if (event.kind === 'expired') return event.data.retry_scheduled
    ? 'The scheduler recorded the expired attempt and scheduled a bounded retry. The job returns to pending; its earlier attempt stays in history.'
    : 'The scheduler recorded the expired attempt. The attempt budget is exhausted, so no further retry is scheduled.';
  if (event.kind === 'succeeded') return 'The current owner’s result and the terminal job transition were committed with their history. Terminal job state is immutable.';
  if (event.kind === 'failed') return event.data.retry_scheduled ? 'The failed attempt was recorded and another eligible attempt was scheduled within the retry budget.' : 'The failure was recorded. No further attempt is scheduled.';
  return 'This transition is recorded in the committed job history. Inspect the raw capture for its complete fields.';
}

export function median(values) {
  if (!values.length || values.some(value => !Number.isFinite(value))) throw new Error('A measurement group is empty or invalid.');
  const sorted = [...values].sort((a, b) => a - b);
  const mid = Math.floor(sorted.length / 2);
  return sorted.length % 2 ? sorted[mid] : (sorted[mid - 1] + sorted[mid]) / 2;
}

export function benchmarkGroups(baseline, candidate) {
  const summarize = runs => ({
    samples: runs.length,
    throughput: median(runs.map(run => run.throughput_jobs_per_second)),
    minimum: Math.min(...runs.map(run => run.throughput_jobs_per_second)),
    maximum: Math.max(...runs.map(run => run.throughput_jobs_per_second)),
    queueP95: median(runs.map(run => run.queue_seconds.p95)) * 1000,
    attemptP95: median(runs.map(run => run.attempt_seconds.p95)) * 1000,
    submitP95: median(runs.map(run => run.submission_seconds.p95)) * 1000,
    inspectP95: median(runs.map(run => run.inspection_seconds.p95)) * 1000,
  });
  return ['short_hash', 'long_timed'].flatMap(workload => [1, 3, 5].map(workers => {
    const matches = run => run.workload === workload && run.workers === workers;
    return { workload, workers, baseline: summarize(baseline.runs.filter(matches)), candidate: summarize(candidate.runs.filter(matches)) };
  }));
}

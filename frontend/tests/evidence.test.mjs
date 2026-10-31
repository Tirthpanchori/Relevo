import test from 'node:test';
import assert from 'node:assert/strict';
import { readFile, readdir } from 'node:fs/promises';
import { resolve } from 'node:path';
import { validateCapture, replayFrame, benchmarkGroups, median } from '../src/lib/evidence.mjs';
const json = async path => JSON.parse(await readFile(new URL(path, import.meta.url), 'utf8'));

test('all replay frames preserve actual committed events and attempts', async () => {
  for (const name of ['worker-crash-recovery', 'component-restarts', 'effect-protected', 'effect-unprotected', 'additional-expiry-diagnostic']) {
    const capture = await json(`../../artifacts/replays/${name}.json`);
    assert.equal(validateCapture(capture), capture);
    capture.events.forEach((event, index) => {
      const frame = replayFrame(capture, index);
      assert.equal(frame.event, event);
      assert.equal(frame.state, event.data.state);
      assert.equal(frame.elapsed, (Date.parse(event.occurred_at) - Date.parse(capture.events[0].occurred_at)) / 1000);
      if (event.attempt_id) assert.equal(frame.attempt.id, event.attempt_id);
    });
    assert.equal(replayFrame(capture, -1).event, capture.events[0]);
    assert.equal(replayFrame(capture, 1000).event, capture.events.at(-1));
  }
});
test('replay rejects absent provenance and invalid history', async () => {
  const capture = await json('../../artifacts/replays/worker-crash-recovery.json');
  assert.throws(() => validateCapture({ ...capture, source: null }));
  assert.throws(() => validateCapture({ ...capture, events: [] }));
  assert.throws(() => validateCapture({ ...capture, events: [{ ...capture.events[0], sequence: 2 }] }));
});
test('chart summaries reproduce retained raw measurements without pooling percentiles', async () => {
  const summary = await json('../public/evidence/benchmark-summary.json');
  let jobs = 0;
  for (const [name, dataset] of Object.entries(summary)) {
    const [base, candidate] = await Promise.all(dataset.rawFiles.map(file => json(`../../benchmarks/raw/${file}.json`)));
    assert.deepEqual(benchmarkGroups(base, candidate), dataset.rows);
    const count = [...base.runs, ...candidate.runs].reduce((n, run) => n + run.jobs.length, 0);
    assert.equal(count, name === 'repeated' ? 1080 : 360);
    jobs += count;
  }
  assert.equal(jobs, 1440);
  assert.equal(summary.confirmation.rows[0].baseline.throughput.toFixed(3), '3.103');
  assert.equal(summary.confirmation.rows[0].candidate.throughput.toFixed(3), '4.001');
  assert.equal(summary.confirmation.rows[5].candidate.throughput.toFixed(3), '5.796');
  assert.equal(median([8, 2, 4, 6]), 5);
  assert.throws(() => median([]));
});
test('built site has six canonical entries, safe local links, and no backend secret', async () => {
  const { site } = await import('../site.mjs');
  const root = resolve(import.meta.dirname, '../dist');
  const sitemap = await readFile(resolve(root, 'sitemap.xml'), 'utf8');
  const locations = [...sitemap.matchAll(/<loc>([^<]+)<\/loc>/g)].map(match => match[1]);
  assert.deepEqual(locations, site.pages.map(({ slug }) => new URL(slug ? `${slug}/` : '', site.canonical).href));
  for (const { slug } of site.pages) {
    const html = await readFile(resolve(root, slug, 'index.html'), 'utf8');
    assert.match(html, /lang="en"/);
    assert.match(html, /\/assets\//);
  }
  const env = await readFile(new URL('../../.env', import.meta.url), 'utf8').catch(() => '');
  const token = env.match(/^RELEVO_API_TOKEN=(.+)$/m)?.[1]?.replace(/^['"]|['"]$/g, '').trim();
  async function scan(directory) {
    for (const entry of await readdir(directory, { withFileTypes: true })) {
      const path = resolve(directory, entry.name);
      if (entry.isDirectory()) await scan(path);
      else if (/\.(js|html|json|txt|md|csv|xml|css)$/.test(entry.name)) {
        const text = await readFile(path, 'utf8');
        if (token?.length > 20) assert.ok(!text.includes(token), 'A private token was included in public files.');
        assert.ok(!text.includes('THESIS: Make the handoff visible.'), 'Internal design contract leaked.');
      }
    }
  }
  await scan(root);
});

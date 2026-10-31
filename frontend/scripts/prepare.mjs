import { mkdir, readFile, writeFile, copyFile } from 'node:fs/promises';
import { resolve, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';
import { site } from '../site.mjs';
import { benchmarkGroups } from '../src/lib/evidence.mjs';

const root = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const repository = resolve(root, '..');
const publicDir = resolve(root, 'public');
const escape = value => value.replaceAll('&', '&amp;').replaceAll('"', '&quot;').replaceAll('<', '&lt;').replaceAll('>', '&gt;');
await mkdir(publicDir, { recursive: true });
for (const page of [...site.pages, { slug: '404', title: 'Relevo — Page not found', description: 'Find your way back to Relevo.' }]) {
  const path = resolve(root, page.slug === '404' ? '404.html' : `${page.slug ? `${page.slug}/` : ''}index.html`);
  await mkdir(dirname(path), { recursive: true });
  const canonical = new URL(page.slug ? `${page.slug}/` : '', site.canonical).href;
  await writeFile(path, `<!doctype html>
<html lang="en"><head><meta charset="UTF-8"/><meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>${escape(page.title)}</title><meta name="description" content="${escape(page.description)}"/>
${page.slug === '404' ? '<meta name="robots" content="noindex"/>' : `<link rel="canonical" href="${escape(canonical)}"/>`}
<meta name="theme-color" content="#10332E"/><link rel="icon" type="image/svg+xml" href="/favicon.svg?v=2"/>
</head><body><div id="root"></div><noscript><main><h1>Relevo</h1><p>${escape(page.description)}</p><p>The interactive explanation needs JavaScript. Read the complete source and documentation at <a href="${site.repository}">the Relevo repository</a>.</p></main></noscript><script type="module" src="/src/main.jsx"></script></body></html>\n`);
}
const files = [
  ['llms.txt', 'llms.txt'],
  ['README.md', 'docs/quickstart.md'],
  ['working.md', 'docs/engine.md'],
  ['decision.md', 'docs/decisions.md'],
  ['benchmarks/README.md', 'docs/benchmarks.md'],
  ['benchmarks/comparison.md', 'evidence/comparison.md'],
  ['benchmarks/confirmation.md', 'evidence/confirmation.md'],
  ['benchmarks/comparison.csv', 'evidence/comparison.csv'],
  ['benchmarks/confirmation.csv', 'evidence/confirmation.csv'],
  ['benchmarks/experiment-notes.md', 'evidence/experiment-notes.md'],
  ['benchmarks/confirmation-notes.md', 'evidence/confirmation-notes.md'],
  ...['baseline-complete', 'monitor-5ms', 'confirmation-awake-50ms', 'confirmation-awake-5ms'].map(name => [`benchmarks/raw/${name}.json`, `evidence/${name}.json`]),
  ...['worker-crash-recovery', 'component-restarts', 'effect-protected', 'effect-unprotected', 'additional-expiry-diagnostic'].map(name => [`artifacts/replays/${name}.json`, `evidence/${name}.json`]),
];
for (const [source, destination] of files) {
  await mkdir(dirname(resolve(publicDir, destination)), { recursive: true });
  await copyFile(resolve(repository, source), resolve(publicDir, destination));
}
const fontLicenses = [['instrument-sans', 'Instrument Sans'], ['ibm-plex-mono', 'IBM Plex Mono']];
let licenses = '';
for (const [name, label] of fontLicenses) {
  licenses += `${label}\n${'='.repeat(label.length)}\n${await readFile(resolve(root, 'node_modules/@fontsource', name, 'LICENSE'), 'utf8')}\n\n`;
}
await writeFile(resolve(publicDir, 'font-licenses.txt'), licenses);
const readJson = async path => JSON.parse(await readFile(resolve(repository, path), 'utf8'));
const repeatedBaseline = await readJson('benchmarks/raw/baseline-complete.json');
const repeatedCandidate = await readJson('benchmarks/raw/monitor-5ms.json');
const confirmationBaseline = await readJson('benchmarks/raw/confirmation-awake-50ms.json');
const confirmationCandidate = await readJson('benchmarks/raw/confirmation-awake-5ms.json');
const dataset = (baseline, candidate, names) => ({
  rows: benchmarkGroups(baseline, candidate),
  baselineRevision: baseline.revision,
  candidateRevision: candidate.revision,
  capturedAt: candidate.captured_at,
  host: baseline.host,
  jobs: [...baseline.runs, ...candidate.runs].reduce((count, run) => count + run.jobs.length, 0),
  rawFiles: names,
});
await writeFile(resolve(publicDir, 'evidence/benchmark-summary.json'), JSON.stringify({
  repeated: dataset(repeatedBaseline, repeatedCandidate, ['baseline-complete', 'monitor-5ms']),
  confirmation: dataset(confirmationBaseline, confirmationCandidate, ['confirmation-awake-50ms', 'confirmation-awake-5ms']),
}, null, 2));
const urls = site.pages.map(({ slug }) => new URL(slug ? `${slug}/` : '', site.canonical).href);
await writeFile(resolve(publicDir, 'sitemap.xml'), `<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n${urls.map(url => `  <url><loc>${escape(url)}</loc></url>`).join('\n')}\n</urlset>\n`);
await writeFile(resolve(publicDir, '.nojekyll'), '');
console.log('Prepared six page entries, the 404, source evidence, font licenses, llms.txt, and sitemap.xml.');

const llm = await readFile(resolve(repository,'llms.txt'),'utf8');
await writeFile(resolve(publicDir,'llms.txt'),llm+'\n## Website\n\n'+site.pages.map(p=>' - ['+(p.slug||'Home')+']('+new URL(p.slug?p.slug+'/':'',site.canonical).href+')').join('\n')+'\n');

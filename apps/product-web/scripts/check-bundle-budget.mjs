#!/usr/bin/env node
/**
 * check:bundle — deterministic page-weight gate (blueprint §1.4 / NB-42.1).
 *
 * Runs after `next build`. For each of the six routes it sums the RAW
 * (uncompressed) byte sizes of every referenced JS chunk (from
 * `.next/app-build-manifest.json` — Next 14 App Router keeps per-route chunk
 * lists there; `.next/build-manifest.json` only covers the pages router),
 * plus the shared `.next/static/css/*.css` and `.next/static/media/*`
 * (self-hosted next/font woff2) totals.
 *
 * Raw size is the conservative proxy for the 1.2 MB transfer budget — gzip
 * transfer is always smaller. Exits 1 when any route ≥ 1,200,000 bytes.
 *
 * The manual 3G devtools measurement (LoadEventEnd < 3s @ 400 kbps) is a
 * separate PR-checklist item (cannot be automated in node).
 */
import { existsSync, readFileSync, readdirSync, statSync } from 'node:fs';
import { join } from 'node:path';

const ROOT = process.cwd();
const NEXT_DIR = join(ROOT, '.next');
const BUDGET_BYTES = 1_200_000;

const ROUTES = [
  { route: '/', key: '/page' },
  { route: '/platform', key: '/platform/page' },
  { route: '/technology', key: '/technology/page' },
  { route: '/pricing', key: '/pricing/page' },
  { route: '/launch', key: '/launch/page' },
  { route: '/contact', key: '/contact/page' },
];

function fail(message) {
  console.error(`\ncheck:bundle FAILED: ${message}`);
  process.exit(1);
}

const manifestPath = join(NEXT_DIR, 'app-build-manifest.json');
if (!existsSync(manifestPath)) {
  fail('app-build-manifest.json not found — run `npm run build` first.');
}

const manifest = JSON.parse(readFileSync(manifestPath, 'utf8'));

function dirBytes(relativeDir) {
  const dir = join(NEXT_DIR, relativeDir);
  if (!existsSync(dir)) return 0;
  return readdirSync(dir).reduce((sum, file) => sum + statSync(join(dir, file)).size, 0);
}

const cssBytes = dirBytes('static/css');
const mediaBytes = dirBytes('static/media');
const sharedBytes = cssBytes + mediaBytes;

/** Chunk paths look like "static/chunks/x.js" (already relative to `.next`). */
function chunkBytes(chunk) {
  const file = join(NEXT_DIR, chunk);
  if (!existsSync(file)) return 0;
  return statSync(file).size;
}

const rows = [];
let failed = false;

for (const { route, key } of ROUTES) {
  const chunks = manifest.pages?.[key];
  if (!Array.isArray(chunks) || chunks.length === 0) {
    fail(`no chunk list in app-build-manifest for route "${route}" (key "${key}")`);
  }

  const jsBytes = chunks
    .filter((chunk) => chunk.endsWith('.js'))
    .reduce((sum, chunk) => sum + chunkBytes(chunk), 0);

  const total = jsBytes + sharedBytes;
  const ok = total < BUDGET_BYTES;
  rows.push({ route, jsBytes, total, ok });
  if (!ok) failed = true;
}

console.log('\ncheck:bundle — per-route RAW byte totals (budget: < 1,200,000 bytes/route)');
console.log(`  shared CSS bytes:    ${cssBytes.toLocaleString('en-US')}`);
console.log(`  shared media bytes:  ${mediaBytes.toLocaleString('en-US')}`);
console.log('  -------------------------------------------------');

for (const row of rows) {
  console.log(
    `  ${row.ok ? 'OK  ' : 'OVER'}  ${row.route.padEnd(12)} js=${row.jsBytes.toLocaleString('en-US')}  total=${row.total.toLocaleString('en-US')}`,
  );
}

if (failed) {
  fail('one or more routes exceed the 1.2 MB page-weight budget.');
}

console.log('\ncheck:bundle PASSED — all six routes under the 1.2 MB budget.\n');

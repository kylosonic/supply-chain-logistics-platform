#!/usr/bin/env node
/**
 * check:bundle — deterministic page-weight gate (blueprint §1.4 / NB-42.1).
 *
 * Runs after `next build`. For each of the eleven routes it sums the RAW
 * (uncompressed) byte sizes of every asset that route actually references, plus
 * the shared CSS and media totals. Exits 1 when any route >= 1,200,000 bytes.
 *
 * Measurement source changed in the Next 16 upgrade (NB-66 follow-up): Next 14
 * and 15 emitted `.next/app-build-manifest.json` with per-route chunk lists;
 * Next 16 no longer emits that file, so this gate failed with
 * "app-build-manifest.json not found".
 *
 * The replacement reads the prerendered HTML in `.next/server/app/**` and
 * extracts the `/_next/...` asset URLs the document references. That is a
 * *better* measurement than the old manifest walk, because it is exactly the
 * set of files the browser downloads for that route — no more (previously
 * over-counted chunks the route did not load) and no less.
 *
 * Raw size is the conservative proxy for the 1.2 MB transfer budget — gzip
 * transfer is always smaller.
 *
 * The manual 3G devtools measurement (LoadEventEnd < 3s @ 400 kbps) is a
 * separate PR-checklist item (cannot be automated in node).
 */
import { existsSync, readFileSync, readdirSync, statSync } from 'node:fs';
import { join } from 'node:path';

const ROOT = process.cwd();
const NEXT_DIR = join(ROOT, '.next');
const APP_SERVER_DIR = join(NEXT_DIR, 'server', 'app');
const BUDGET_BYTES = 1_200_000;

/**
 * route -> prerendered HTML file relative to `.next/server/app`.
 * `/` is `index.html`; every other route is `<segment>.html`.
 */
const ROUTES = [
  { route: '/', html: 'index.html' },
  { route: '/platform', html: 'platform.html' },
  { route: '/technology', html: 'technology.html' },
  { route: '/pricing', html: 'pricing.html' },
  { route: '/launch', html: 'launch.html' },
  { route: '/contact', html: 'contact.html' },
  { route: '/docs', html: 'docs.html' },
  { route: '/privacy', html: 'privacy.html' },
  { route: '/terms', html: 'terms.html' },
  { route: '/security', html: 'security.html' },
  { route: '/status', html: 'status.html' },
];

function fail(message) {
  console.error(`\ncheck:bundle FAILED: ${message}`);
  process.exit(1);
}

if (!existsSync(APP_SERVER_DIR)) {
  fail('.next/server/app not found — run `npm run build` first.');
}

// Next 16 may or may not emit app-build-manifest.json depending on version and
// builder. Prefer it when present (cheap), otherwise fall back to HTML parsing.
const manifestPath = join(NEXT_DIR, 'app-build-manifest.json');
const manifest = existsSync(manifestPath)
  ? JSON.parse(readFileSync(manifestPath, 'utf8'))
  : null;

function dirBytes(relativeDir) {
  const dir = join(NEXT_DIR, relativeDir);
  if (!existsSync(dir)) return 0;
  return readdirSync(dir).reduce((sum, file) => sum + statSync(join(dir, file)).size, 0);
}

const cssBytes = dirBytes('static/css');
const mediaBytes = dirBytes('static/media');
const sharedBytes = cssBytes + mediaBytes;

/** `/_next/static/chunks/x.js` -> byte size of that file inside `.next`. */
function assetBytes(url) {
  const relative = url.replace(/^\/_next\//, '');
  const file = join(NEXT_DIR, relative);
  if (!existsSync(file)) return 0;
  return statSync(file).size;
}

/** Collect the unique `/_next/...` asset URLs a prerendered HTML file references. */
function assetsFromHtml(htmlPath) {
  if (!existsSync(htmlPath)) return null;
  const html = readFileSync(htmlPath, 'utf8');
  const urls = new Set();
  // Matches src="/_next/..." and href="/_next/..." (script, stylesheet, preload).
  for (const match of html.matchAll(/(?:src|href)="(\/_next\/[^"]+)"/g)) {
    urls.add(match[1].split('?')[0]);
  }
  return [...urls];
}

const rows = [];
let failed = false;

for (const { route, html } of ROUTES) {
  let assetUrls = null;

  if (manifest) {
    const key = route === '/' ? '/page' : `${route}/page`;
    const chunks = manifest.pages?.[key];
    if (Array.isArray(chunks) && chunks.length > 0) {
      assetUrls = chunks.map((chunk) => `/_next/${chunk}`);
    }
  }

  if (!assetUrls) {
    assetUrls = assetsFromHtml(join(APP_SERVER_DIR, html));
  }

  if (!assetUrls || assetUrls.length === 0) {
    fail(
      `could not determine the assets for route "${route}" — ` +
        `neither app-build-manifest.json nor .next/server/app/${html} listed any. ` +
        `If the build output layout changed again, update this script.`,
    );
  }

  // Only .js counts as route JS; CSS is already covered by the shared total.
  const jsBytes = assetUrls
    .filter((url) => url.endsWith('.js'))
    .reduce((sum, url) => sum + assetBytes(url), 0);

  const total = jsBytes + sharedBytes;
  const ok = total < BUDGET_BYTES;
  rows.push({ route, jsBytes, total, ok });
  if (!ok) failed = true;
}

console.log('\ncheck:bundle — per-route RAW byte totals (budget: < 1,200,000 bytes/route)');
console.log(`  source:              ${manifest ? 'app-build-manifest.json' : 'prerendered HTML assets'}`);
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

console.log('\ncheck:bundle PASSED — all eleven routes under the 1.2 MB budget.\n');

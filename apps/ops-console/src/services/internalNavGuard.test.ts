import { readdirSync, readFileSync, statSync } from 'node:fs';
import { join, relative } from 'node:path';
import { fileURLToPath } from 'node:url';
import { describe, expect, it } from 'vitest';

/** `apps/ops-console/src` resolved from this test file, independent of cwd. */
const SRC_DIR = fileURLToPath(new URL('..', import.meta.url));

/** This guard file itself contains the pattern as a regression literal. */
const SELF = fileURLToPath(import.meta.url);

function sourceFiles(dir: string): string[] {
  const out: string[] = [];
  for (const entry of readdirSync(dir)) {
    const full = join(dir, entry);
    if (statSync(full).isDirectory()) {
      out.push(...sourceFiles(full));
    } else if (/\.(ts|tsx)$/.test(entry) && full !== SELF) {
      out.push(full);
    }
  }
  return out;
}

describe('internal navigation guard (NB-54 / NB-59)', () => {
  it('contains no raw `<a href="/...">` internal anchors anywhere in src (NB-54.1/.2)', () => {
    const offenders = sourceFiles(SRC_DIR)
      .filter((file) => /<a\s+href="\//.test(readFileSync(file, 'utf8')))
      .map((file) => relative(SRC_DIR, file));

    expect(offenders).toEqual([]);
  });

  it('preserves the external OpenStreetMap attribution anchor in RouteMap (NB-54.3)', () => {
    const content = readFileSync(join(SRC_DIR, 'components', 'RouteMap.tsx'), 'utf8');
    expect(content).toContain('https://www.openstreetmap.org/copyright');
  });

  it('points the LoginPage signup fallback at the real product site (NB-59.5)', () => {
    const content = readFileSync(join(SRC_DIR, 'pages', 'LoginPage.tsx'), 'utf8');
    expect(content).toContain('https://product-web-chi.vercel.app/launch');
  });
});

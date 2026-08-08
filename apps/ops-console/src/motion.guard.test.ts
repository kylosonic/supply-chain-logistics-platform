import { readFileSync, readdirSync, statSync } from 'node:fs';
import { join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { describe, expect, it } from 'vitest';

/** `apps/ops-console/src` resolved from this test file, independent of cwd. */
const SRC_DIR = fileURLToPath(new URL('.', import.meta.url));

/** This guard file itself contains the patterns as regression literals. */
const SELF = fileURLToPath(import.meta.url);

function read(rel: string): string {
  return readFileSync(join(SRC_DIR, rel), 'utf8');
}

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

describe('page-mount animation guard (TECH-74 / NB-57)', () => {
  it('removes every animationDelay and stagger- usage from src (rows 4, 6, 8, 11, 14, 16, 19, 21)', () => {
    const offenders: string[] = [];
    for (const file of sourceFiles(SRC_DIR)) {
      const content = readFileSync(file, 'utf8');
      if (content.includes('animationDelay') || content.includes('stagger-')) {
        offenders.push(file);
      }
    }
    expect(offenders).toEqual([]);
  });

  it('confines animate-* page-mount classes to index.css utilities + the RouteOptimizerForm results container (rows 1-23)', () => {
    const allowed = new Set([
      join(SRC_DIR, 'index.css'),
      join(SRC_DIR, 'components', 'RouteOptimizerForm.tsx'),
    ]);
    const offenders: string[] = [];
    for (const file of sourceFiles(SRC_DIR)) {
      const content = readFileSync(file, 'utf8');
      if (/(animate-fade-in|animate-scale-in|animate-slide-up)/.test(content) && !allowed.has(file)) {
        offenders.push(file);
      }
    }
    expect(offenders).toEqual([]);
  });

  it('keeps the RouteOptimizerForm state-change animation only — animate-slide-up container, no animationDelay (rows 20-21)', () => {
    const source = read('components/RouteOptimizerForm.tsx');
    expect(source.split('animate-slide-up').length - 1).toBe(1);
    expect(source).not.toContain('animationDelay');
  });

  it('index.css: .fp-row animation stripped, .stagger-* deleted, .fp-page-fade added, dialog + reduced-motion kept (rows 22-26)', () => {
    const css = read('index.css');
    const fpRowBlock = css.slice(css.indexOf('.fp-row {'), css.indexOf('.fp-row:hover'));
    expect(fpRowBlock).not.toContain('animation:');
    expect(css).not.toContain('.stagger-');
    expect(css).toMatch(/\.fp-page-fade\s*\{\s*animation: fadeIn 0\.14s ease-out both;\s*\}/);
    expect(css).toContain('.fp-dialog-overlay');
    expect(css).toContain('.fp-dialog-surface');
    expect(css).toContain('animation: fadeIn 0.3s ease-out both;');
    expect(css).toContain('animation: scaleIn 0.28s ease-out both;');
    expect(css).toContain('prefers-reduced-motion');
  });
});

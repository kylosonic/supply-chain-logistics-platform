import { readFileSync } from 'node:fs';
import { join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { describe, expect, it } from 'vitest';

/**
 * Static guard over `index.css` (NB-62 regression-guard seed; TECH-79 extends).
 * Proves the five shared surface classes reference the design-system tokens
 * and that no slate overlay classes have silently returned. Content-level
 * proof only — no DOM, no Tailwind compilation.
 *
 * Blueprint: `docs/plans/phase-console-login-color-fidelity-01-token-surfaces.md`
 * §2.1, §2.3, §5.2.
 */

/** `apps/ops-console/src` resolved from this test file, independent of cwd. */
const SRC_DIR = fileURLToPath(new URL('.', import.meta.url));

function readIndexCss(): string {
  return readFileSync(join(SRC_DIR, 'index.css'), 'utf8');
}

/** Slice of the css between `<selector> {` and its first closing brace. */
function classBlock(css: string, selector: string): string {
  const start = css.indexOf(`${selector} {`);
  if (start === -1) {
    throw new Error(`Selector not found in index.css: ${selector}`);
  }
  return css.slice(start, css.indexOf('}', start));
}

/** The token block: the `:root` that declares `--fp-*` variables. */
function tokenBlock(css: string): string {
  const start = css.indexOf('--fp-black');
  if (start === -1) {
    throw new Error('Token block not found in index.css (no --fp-black)');
  }
  return css.slice(start, css.indexOf('}', start));
}

const FIVE_CLASSES = [
  '.fp-shell-surface',
  '.fp-nested-surface',
  '.fp-pill',
  '.fp-input',
  '.fp-row',
] as const;

/** Mandated token references per class (blueprint §2.1). */
const TOKEN_EXPECTATIONS: Readonly<Record<(typeof FIVE_CLASSES)[number], { bg: string; border: string }>> = {
  '.fp-shell-surface': { bg: 'var(--fp-surface)', border: 'var(--fp-border)' },
  '.fp-nested-surface': { bg: 'var(--fp-elevated)', border: 'var(--fp-border)' },
  '.fp-pill': { bg: 'var(--fp-elevated)', border: 'var(--fp-border)' },
  '.fp-input': { bg: 'var(--fp-input)', border: 'var(--fp-border)' },
  '.fp-row': { bg: 'var(--fp-elevated)', border: 'var(--fp-border)' },
};

const FORBIDDEN_SLATE_OVERLAYS = ['bg-slate-950', 'bg-slate-900', 'bg-slate-800', 'bg-slate-700'] as const;

describe('shared surface token guard (TECH-77 / NB-60, NB-62 seed)', () => {
  it('declares the --fp-placeholder token in :root', () => {
    expect(tokenBlock(readIndexCss())).toContain('--fp-placeholder: #94a3b8;');
  });

  it.each(FIVE_CLASSES.map((selector) => [selector]))(
    'retokenizes %s to its design-system tokens (no slate overlays)',
    (selector) => {
      const css = readIndexCss();
      const block = classBlock(css, selector);
      const expected = TOKEN_EXPECTATIONS[selector];
      expect(block).toContain(`background-color: ${expected.bg};`);
      expect(block).toContain(`border-color: ${expected.border};`);
      for (const forbidden of FORBIDDEN_SLATE_OVERLAYS) {
        expect(block).not.toContain(forbidden);
      }
    },
  );

  it('colors .fp-input text with --fp-primary and its placeholder with --fp-placeholder', () => {
    const css = readIndexCss();
    expect(classBlock(css, '.fp-input')).toContain('color: var(--fp-primary);');
    expect(classBlock(css, '.fp-input::placeholder')).toContain('color: var(--fp-placeholder);');
  });
});

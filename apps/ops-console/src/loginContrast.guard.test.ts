import { readFileSync } from 'node:fs';
import { join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { describe, expect, it } from 'vitest';

/**
 * Static guard over the login-page text colors (TECH-78 / NB-61; NB-62
 * guard's text-side seed). Proves the two low-contrast slate utilities are
 * gone from both login files, that the AA-passing `text-slate-400` (7.22:1 on
 * shell, 6.83:1 on elevated — pinned in `services/contrastRatio.test.ts`) is
 * what replaced them, that the bootstrap `hover:text-slate-300` state is
 * preserved, and that rose stays confined to the error panels. Content-level
 * proof only — no DOM, no Tailwind compilation.
 *
 * Blueprint: `docs/plans/phase-console-login-color-fidelity-02-login-contrast.md`
 * §2.2, §2.3, §3, §5.2. Deliberately does not assert copy.
 */

/** `apps/ops-console/src` resolved from this test file, independent of cwd. */
const SRC_DIR = fileURLToPath(new URL('.', import.meta.url));

function readLoginPage(): string {
  return readFileSync(join(SRC_DIR, 'pages', 'LoginPage.tsx'), 'utf8');
}

function readLoginFeedbackPanels(): string {
  return readFileSync(join(SRC_DIR, 'components', 'login', 'LoginFeedbackPanels.tsx'), 'utf8');
}

const BANNED_LOW_CONTRAST_UTILITIES = ['text-slate-500', 'text-slate-600'] as const;

const LOGIN_FILES: ReadonlyArray<{ name: string; read: () => string }> = [
  { name: 'LoginPage.tsx', read: readLoginPage },
  { name: 'LoginFeedbackPanels.tsx', read: readLoginFeedbackPanels },
];

describe('login text-color guard (TECH-78 / NB-61, NB-62 text-side seed)', () => {
  it.each(LOGIN_FILES.map(({ name }) => [name]))(
    'bans low-contrast text utilities from %s',
    (name) => {
      const source = LOGIN_FILES.find((f) => f.name === name)!.read();
      for (const banned of BANNED_LOW_CONTRAST_UTILITIES) {
        expect(source).not.toContain(banned);
      }
    },
  );

  it('LoginPage.tsx uses text-slate-400 for its small text', () => {
    expect(readLoginPage()).toContain('text-slate-400');
  });

  it('LoginPage.tsx preserves the bootstrap hover:text-slate-300 state', () => {
    expect(readLoginPage()).toContain('hover:text-slate-300');
  });

  it('LoginFeedbackPanels.tsx keeps rose-300 for error states', () => {
    expect(readLoginFeedbackPanels()).toContain('text-rose-300');
  });
});

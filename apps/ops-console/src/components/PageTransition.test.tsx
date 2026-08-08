import { readFileSync } from 'node:fs';
import { renderToString } from 'react-dom/server';
import { StaticRouter } from 'react-router-dom/server';
import { describe, expect, it } from 'vitest';

import { PageTransition } from './PageTransition';

describe('PageTransition (TECH-74 / NB-57)', () => {
  it('first render suppresses the fade class and renders the page children (NB-57.1, first-login-load)', () => {
    const html = renderToString(
      <StaticRouter location="/alerts">
        <PageTransition>
          <div data-testid="page-surface">Alerts surface</div>
        </PageTransition>
      </StaticRouter>,
    );

    expect(html).not.toContain('fp-page-fade');
    expect(html).toContain('data-testid="page-surface"');
    expect(html).toContain('Alerts surface');
  });

  it('keys the wrapper by pathname and applies the fade class after the first commit — source guards', () => {
    const source = readFileSync(new URL('./PageTransition.tsx', import.meta.url), 'utf8');

    expect(source).toContain('key={pathname}');
    expect(source).toContain('fp-page-fade');
    // Mount-only effect flips the suppression flag (never written during render — StrictMode-safe).
    expect(source).toMatch(/useEffect\(\s*\(\)\s*=>\s*\{\s*suppressMountRef\.current = false;\s*\},\s*\[\]\)/);
  });
});

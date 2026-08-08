import { readFileSync } from 'node:fs';
import { renderToString } from 'react-dom/server';
import { StaticRouter } from 'react-router-dom/server';
import { describe, expect, it } from 'vitest';

import { ScrollManager } from './ScrollManager';

describe('ScrollManager (TECH-75 / NB-58)', () => {
  it('renders nothing (null) in SSR without crashing', () => {
    const html = renderToString(
      <StaticRouter location="/alerts">
        <ScrollManager />
      </StaticRouter>,
    );

    expect(html).toBe('');
  });

  it('restores the saved position on POP and starts at top otherwise — source guards (NB-58.1, NB-58.2)', () => {
    const source = readFileSync(new URL('./ScrollManager.tsx', import.meta.url), 'utf8');

    expect(source).toContain('useLocation');
    expect(source).toContain('useNavigationType');
    expect(source).toContain("import { createScrollPositions } from '../services/scrollPositions';");
    expect(source).toContain("navigationType === 'POP'");
    expect(source).toContain('saved ?? 0');
    expect(source).toContain('window.scrollTo(0, 0)');
    // Store created exactly once per app lifetime (pure factory behind a ref).
    expect(source).toMatch(/useRef<ScrollPositions \| null>\(null\)/);
  });
});

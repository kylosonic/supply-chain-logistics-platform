import { renderToString } from 'react-dom/server';
import { describe, expect, it, vi } from 'vitest';

vi.mock('./services', () => ({
  companySignup: vi.fn(),
}));

import App from './App';

describe('product-web overhaul smoke', () => {
  it('renders the enterprise control-tower hero and workspace signup call to action', () => {
    const html = renderToString(<App />);

    expect(html).toContain('Decision intelligence for teams that cannot afford reactive dispatch.');
    expect(html).toContain('Create company workspace');
    expect(html).toContain('FreightPilot Control Stack');
  });
});
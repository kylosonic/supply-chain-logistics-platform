import { renderToString } from 'react-dom/server';
import { StaticRouter } from 'react-router-dom/server';
import { describe, expect, it, vi } from 'vitest';

import { DashboardPage } from './DashboardPage';
import { LoginPage } from './LoginPage';

vi.mock('../context/AuthContext', () => ({
  useAuth: () => ({
    token: 'test-token',
    user: { email: 'ops@testco.com', username: 'ops', role: 'admin' },
    isAuthenticated: false,
    isLoading: false,
    login: vi.fn(),
    logout: vi.fn(),
  }),
}));

vi.mock('../hooks/useLiveUpdates', () => ({
  useLiveUpdates: () => undefined,
}));

describe('ops console surface smoke', () => {
  it('renders the redesigned login workstation shell', () => {
    const html = renderToString(
      <StaticRouter location="/login">
        <LoginPage />
      </StaticRouter>,
    );

    expect(html).toContain('Enter control tower');
    expect(html).toContain('Operator access to routes, exceptions, launch readiness, and billing control.');
  });

  it('renders the control-tower dashboard shell without executing live effects', () => {
    const html = renderToString(
      <StaticRouter location="/">
        <DashboardPage />
      </StaticRouter>,
    );

    expect(html).toContain('Operations command surface');
    expect(html).toContain('Loading dashboard...');
  });
});
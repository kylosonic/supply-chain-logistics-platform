import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { renderToString } from 'react-dom/server';
import { StaticRouter } from 'react-router-dom/server';
import { describe, expect, it, vi } from 'vitest';

import { DashboardPage } from './DashboardPage';
import { LoginPage } from './LoginPage';

vi.mock('../context/AuthContext', () => ({
  useAuth: () => ({
    getToken: () => Promise.resolve(null),
    user: null,
    isAuthenticated: false,
    isLoading: false,
    login: vi.fn(),
    logout: vi.fn(),
  }),
}));

const queryClient = new QueryClient({
  defaultOptions: { queries: { retry: false } },
});

describe('ops console surface smoke', () => {
  it('renders the redesigned login workstation shell', () => {
    const html = renderToString(
      <QueryClientProvider client={queryClient}>
        <StaticRouter location="/login">
          <LoginPage />
        </StaticRouter>
      </QueryClientProvider>,
    );

    expect(html).toContain('Enter control tower');
  });

  it('renders the control-tower dashboard skeleton during data fetch', () => {
    const html = renderToString(
      <QueryClientProvider client={queryClient}>
        <StaticRouter location="/">
          <DashboardPage />
        </StaticRouter>
      </QueryClientProvider>,
    );

    expect(html).toContain('animate-pulse');
  });
});

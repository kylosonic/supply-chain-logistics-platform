import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { renderToString } from 'react-dom/server';
import { StaticRouter } from 'react-router-dom/server';
import { describe, expect, it, vi } from 'vitest';

import { DashboardPage } from './DashboardPage';
import { LoginPage } from './LoginPage';
import { ReceiptsPage } from './ReceiptsPage';
import { AdminReceiptsPage } from './AdminReceiptsPage';

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

vi.mock('../services/receiptsApi', async (importOriginal) => {
  const actual = await importOriginal<typeof import('../services/receiptsApi')>();
  return {
    ...actual,
    uploadReceipt: vi.fn(),
    getReceiptFileUrl: vi.fn(),
    renderDecision: vi.fn(),
    submitDispute: vi.fn(),
  };
});

vi.mock('../services/api', async (importOriginal) => {
  const actual = await importOriginal<typeof import('../services/api')>();
  return {
    ...actual,
    api: {
      get: vi.fn(() => Promise.resolve({ data: [] })),
      post: vi.fn(() => Promise.resolve({ data: {} })),
    },
  };
});

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

  it('renders the customer receipts surface', () => {
    const html = renderToString(
      <QueryClientProvider client={queryClient}>
        <StaticRouter location="/receipts">
          <ReceiptsPage />
        </StaticRouter>
      </QueryClientProvider>,
    );

    expect(html).toContain('Upload a transfer receipt');
    expect(html).toContain('Receipts and wallet');
  });

  it('renders the admin verification queue surface', () => {
    const html = renderToString(
      <QueryClientProvider client={queryClient}>
        <StaticRouter location="/admin/receipts">
          <AdminReceiptsPage />
        </StaticRouter>
      </QueryClientProvider>,
    );

    expect(html).toContain('Receipt verdicts');
    expect(html).toContain('No receipts awaiting a verdict.');
  });
});

import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { renderToString } from 'react-dom/server';
import { Route, Routes } from 'react-router-dom';
import { StaticRouter } from 'react-router-dom/server';
import { describe, expect, it, vi } from 'vitest';

import { Layout } from './Layout';
import App from '../App';
import type { ActivationState } from '../types/api';

const { authMocks } = vi.hoisted(() => ({
  authMocks: { logout: vi.fn() },
}));

vi.mock('../context/AuthContext', () => ({
  useAuth: () => ({
    user: {
      id: 'user-1',
      username: 'captain',
      email: 'captain@testco.com',
      full_name: 'Captain Test',
      role: 'operator',
      is_active: true,
      created_at: '2026-08-08T00:00:00Z',
    },
    logout: authMocks.logout,
    getToken: () => Promise.resolve('test-token'),
    isAuthenticated: true,
    isLoading: false,
  }),
}));

function p60PitchState(): ActivationState {
  return {
    organization_id: 'org-1',
    n_of_5: 0,
    pct_complete: 0,
    milestones: [
      { category: 'warehouses', label: 'Warehouses', status: 'sample', real_rows: 0, sample_rows: 2, completed: false },
      { category: 'items', label: 'Items', status: 'sample', real_rows: 0, sample_rows: 2, completed: false },
      { category: 'fleet_assets', label: 'Fleet Assets', status: 'sample', real_rows: 0, sample_rows: 2, completed: false },
      { category: 'inventory', label: 'Inventory', status: 'sample', real_rows: 0, sample_rows: 2, completed: false },
      { category: 'orders', label: 'Orders', status: 'sample', real_rows: 0, sample_rows: 2, completed: false },
    ],
    m6_completed: false,
    m6_completed_at: null,
    next_step: { category: 'warehouses', label: 'Warehouses', cta: '/upload' },
    banner: { visible: true, n_of_5: 0, pct_complete: 0, cta: '/upload', demo_mode: true },
    free_cap: { locked: false, utilization_pct: 0, message: null },
    pitch: { banner: 'p60', dismissible: true, fired: ['p60'] },
    toast_fired: false,
  };
}

describe('Layout shell smoke (TECH-72 / NB-55)', () => {
  it('renders the full persistent shell under the layout-route structure', () => {
    const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
    queryClient.setQueryData(['activation'], p60PitchState());

    const html = renderToString(
      <QueryClientProvider client={queryClient}>
        <StaticRouter location="/">
          <Routes>
            <Route path="/" element={<Layout />} />
          </Routes>
        </StaticRouter>
      </QueryClientProvider>,
    );

    // Sidebar brand block (NB-55.1).
    expect(html).toContain('FreightPilot');
    expect(html).toContain('Operations workspace');
    // Both navigation groups + codes.
    expect(html).toContain('Control Tower');
    expect(html).toContain('Route Studio');
    expect(html).toContain('Shipments');
    expect(html).toContain('Exceptions');
    expect(html).toContain('Planning');
    expect(html).toContain('Data Intake');
    expect(html).toContain('Payments');
    expect(html).toContain('Verification Queue');
    expect(html).toContain('Integrations');
    expect(html).toContain('CT');
    expect(html).toContain('RT');
    expect(html).toContain('SH');
    expect(html).toContain('EX');
    expect(html).toContain('PL');
    expect(html).toContain('DI');
    expect(html).toContain('PY');
    expect(html).toContain('VQ');
    expect(html).toContain('WS');
    expect(html).toContain('IN');
    // Identity footer + logout (NB-55.1).
    expect(html).toContain('Logout');
    expect(html).toContain('captain@testco.com');
    expect(html).toContain('operator');
    // Top shell: context label + descriptor (NB-55.2).
    expect(html).toContain('Control tower');
    expect(html).toContain('Routes, exceptions, planning, and workspace governance.');
    // Persistent banner mounted inside the shell (NB-55.3).
    expect(html).toContain('data-testid="cap-pitch-banner"');
    // The Outlet content slot exists for page switching.
    expect(html).toContain('<main');
  });

  it('keeps the shell mounted while a lazy page chunk suspends (decision 2)', () => {
    const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
    queryClient.setQueryData(['activation'], p60PitchState());

    // App renders <Routes> → the auth-only layout route. The dashboard index
    // chunk is lazy and cannot resolve during renderToString, so the NESTED
    // Suspense inside Layout must show the surface fallback while the shell
    // (sidebar/header/banner) stays mounted.
    const html = renderToString(
      <QueryClientProvider client={queryClient}>
        <StaticRouter location="/">
          <App />
        </StaticRouter>
      </QueryClientProvider>,
    );

    expect(html).toContain('FreightPilot'); // shell mounted
    expect(html).toContain('data-testid="cap-pitch-banner"'); // banner mounted
    expect(html).toContain('Loading workspace surface...'); // nested fallback, not a shell remount
  });
});

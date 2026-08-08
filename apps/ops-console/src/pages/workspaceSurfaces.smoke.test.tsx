import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { renderToString } from 'react-dom/server';
import { StaticRouter } from 'react-router-dom/server';
import { describe, expect, it, vi } from 'vitest';

import { DashboardPage } from './DashboardPage';
import { LoginPage } from './LoginPage';
import { ReceiptsPage } from './ReceiptsPage';
import { AdminReceiptsPage } from './AdminReceiptsPage';
import { AccountPage } from './AccountPage';
import { RoutesPage } from './RoutesPage';
import { UploadPage } from './UploadPage';
import { ShipmentsPage } from './ShipmentsPage';
import { AlertsPage } from './AlertsPage';
import { PlanningPage } from './PlanningPage';
import { ProvidersPage } from './ProvidersPage';
import { UnauthorizedPage } from './UnauthorizedPage';
import { WorkspaceResetDangerZone } from '../components/WorkspaceResetDangerZone';
import type { ActivationState } from '../types/api';

const { authUserState } = vi.hoisted(() => ({
  authUserState: { user: null as { role: string; email?: string; username?: string } | null },
}));

vi.mock('../context/AuthContext', () => ({
  useAuth: () => ({
    getToken: () => Promise.resolve(null),
    user: authUserState.user,
    isAuthenticated: Boolean(authUserState.user),
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

// leaflet touches `window` at module load, which is undefined in the node
// test environment — the Route Studio smoke block must not execute it.
// Test-scoped only; no runtime modules are mocked.
vi.mock('leaflet', () => ({
  default: {
    icon: () => ({
      iconRetinaUrl: '',
      iconUrl: '',
      shadowUrl: '',
      iconSize: [0, 0],
      iconAnchor: [0, 0],
    }),
  },
  icon: () => ({}),
}));

vi.mock('react-leaflet', () => ({
  MapContainer: () => null,
  Marker: () => null,
  Polygon: () => null,
  Polyline: () => null,
  Popup: () => null,
  TileLayer: () => null,
}));

function seededActivationState(): ActivationState {
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
    pitch: { banner: null, dismissible: false, fired: [] },
    toast_fired: false,
  };
}

const queryClient = new QueryClient({
  defaultOptions: { queries: { retry: false } },
});

/** react-dom/server inserts `<!-- -->` at JSX expression boundaries;
 * strip them so copy assertions read as authored text. */
function strip(html: string): string {
  return html.replace(/<!-- -->/g, '');
}

/** QueryClient preloaded with a seeded 0-of-5 dashboard state. */
function preloadedDashboardClient(): QueryClient {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  client.setQueryData(['activation'], seededActivationState());
  client.setQueryData(['inventory', 'overview'], []);
  client.setQueryData(['forecast', 4], { horizon_weeks: 4, model_name: 'mock', points: [] });
  client.setQueryData(['routes', 'schedules'], []);
  client.setQueryData(['shipments'], []);
  client.setQueryData(['planning', 'replenishment'], []);
  client.setQueryData(['subscriptions', 'usage'], {
    metric: 'delivery_tasks',
    period_start: '2026-08-01',
    period_end: '2026-08-31',
    included_units: 2500,
    used_units: 0,
    overage_units: 0,
    utilization_percent: 0,
    estimated_overage_cost_usd: null,
  });
  client.setQueryData(['ops', 'exception-feed'], {
    summary: { open_alerts: 0, delayed_shipments: 0, pending_replenishment_plans: 0, route_runs_with_unassigned_deliveries: 0 },
    items: [],
  });
  client.setQueryData(['ops', 'audit-timeline'], []);
  client.setQueryData(['weather', 'risk-zones'], []);
  client.setQueryData(['ops', 'dock-appointments'], []);
  return client;
}

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
    expect(html).toContain('Create company account');
    expect(html).toContain('Create initial admin (first-time setup)');
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

  it('renders the admin reversals panel (Verified & reversible)', () => {
    const html = renderToString(
      <QueryClientProvider client={queryClient}>
        <StaticRouter location="/admin/receipts">
          <AdminReceiptsPage />
        </StaticRouter>
      </QueryClientProvider>,
    );

    // React SSR escapes the ampersand in the panel title.
    expect(html).toContain('Verified &amp; reversible');
    expect(html).toContain('No verified receipts.');
  });

  it('renders the queue without the fraud badge chip when no flag is present', () => {
    const html = renderToString(
      <QueryClientProvider client={queryClient}>
        <StaticRouter location="/admin/receipts">
          <AdminReceiptsPage />
        </StaticRouter>
      </QueryClientProvider>,
    );

    // The mocked api returns an empty queue — no sender flag can be present.
    expect(html).not.toContain('reversed credit on file');
  });

  it('renders the seeded dashboard with the activation banner and gate placeholders (0-of-5)', () => {
    const client = preloadedDashboardClient();
    const html = renderToString(
      <QueryClientProvider client={client}>
        <StaticRouter location="/">
          <DashboardPage />
        </StaticRouter>
      </QueryClientProvider>,
    );

    expect(html).toContain('data-testid="activation-banner"');
    expect(strip(html)).toContain('You&#x27;re 0% through onboarding');
    expect(html).toContain('Unlocks after Milestone');
    expect(html).toContain('Continue onboarding');
  });

  it('renders the 0% activation banner on `/` after a reset + re-login (NB-35.7)', () => {
    // The reset flow (covered in ActivationBanner.test.tsx) wipes the query
    // cache and redirects to /login; the next login lands on `/` with the
    // freshly-seeded 0-of-5 state — the default landing renders the 0% banner.
    const client = preloadedDashboardClient();
    const html = renderToString(
      <QueryClientProvider client={client}>
        <StaticRouter location="/">
          <DashboardPage />
        </StaticRouter>
      </QueryClientProvider>,
    );

    expect(strip(html)).toContain('You&#x27;re 0% through onboarding');
    expect(html).toContain('data-testid="activation-banner"');
    expect(html).toContain('href="/upload"');
  });

  it('renders the two-tier dashboard metric hierarchy with milestone-5 locked variants (0-of-5)', () => {
    const client = preloadedDashboardClient();
    const html = renderToString(
      <QueryClientProvider client={client}>
        <StaticRouter location="/">
          <DashboardPage />
        </StaticRouter>
      </QueryClientProvider>,
    );

    // Primary pair and secondary trio copy all render (source plan §5 Layer C).
    expect(html).toContain('Open exceptions');
    expect(html).toContain('In-transit');
    expect(html).toContain('Forecast demand');
    expect(html).toContain('Weather risk');
    expect(html).toContain('Usage posture');
    // Seeded 0-of-5: forecast + weather render their locked milestone-5 variants.
    expect(html).toContain('>Locked<');
    expect(html).toContain('Unlocks after Milestone 5.');
    expect(html).toContain('Continue onboarding');
  });

  it('renders the Route Studio workstation surfaces (form, map placeholder, library, history)', () => {
    const html = renderToString(
      <QueryClientProvider client={queryClient}>
        <StaticRouter location="/routes">
          <RoutesPage />
        </StaticRouter>
      </QueryClientProvider>,
    );

    expect(html).toContain('Route studio');
    expect(html).toContain('Build, compare, and operationalize route scenarios');
    expect(html).toContain('Optimize route');
    expect(html).toContain('Schedule library');
    expect(html).toContain('Scenario history');
    // No activation data resolves to milestone 0 — the locked map placeholder renders.
    expect(html).toContain('Unlocks after Milestone 5');
    expect(html).toContain('No optimization history');
  });

  it('renders the account page with the escalation contact phone field (PROD-03)', () => {
    const html = renderToString(
      <QueryClientProvider client={queryClient}>
        <StaticRouter location="/account">
          <AccountPage />
        </StaticRouter>
      </QueryClientProvider>,
    );

    expect(strip(html)).toContain('Escalation contact');
    expect(html).toContain('placeholder="Escalation phone"');
    expect(html).toContain('Save phone number');
  });

  it('renders the admin danger zone with typed-confirmation reset (disabled until match)', () => {
    const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
    authUserState.user = { role: 'admin', email: 'admin@seedco.com' };

    const html = renderToString(
      <QueryClientProvider client={client}>
        <StaticRouter location="/account">
          <WorkspaceResetDangerZone organizationName="Seed Co" isAdmin defaultOpen />
        </StaticRouter>
      </QueryClientProvider>,
    );

    expect(html).toContain('Reset workspace to sample data');
    expect(html).toContain('role="dialog"');
    expect(html).toContain('Seed Co');
    expect(html).toContain('disabled=""'); // confirm disabled until the typed name matches
  });

  it('hides the danger zone from non-admin users', () => {
    const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
    const html = renderToString(
      <QueryClientProvider client={client}>
        <StaticRouter location="/account">
          <WorkspaceResetDangerZone organizationName="Seed Co" isAdmin={false} />
        </StaticRouter>
      </QueryClientProvider>,
    );

    expect(html).not.toContain('Reset workspace to sample data');
  });

  it('renders the upload intake surface with the calm import rail and per-spec actions', () => {
    const html = renderToString(
      <QueryClientProvider client={queryClient}>
        <StaticRouter location="/upload">
          <UploadPage />
        </StaticRouter>
      </QueryClientProvider>,
    );

    expect(html).toContain('Load a workspace in the right operational order');
    expect(html).toContain('Recommended onboarding order');
    // Unseeded activation resolves to an unlocked free cap, so the action labels render.
    expect(html).toContain('Upload Warehouses');
    expect(html).toContain('Upload Items');
    expect(html).toContain('Upload Fleet Assets');
    expect(html).toContain('Upload Inventory');
    expect(html).toContain('Upload Orders');
  });

  it('renders the shipments surface with the labeled manual-entry form', () => {
    const html = renderToString(
      <QueryClientProvider client={queryClient}>
        <StaticRouter location="/shipments">
          <ShipmentsPage />
        </StaticRouter>
      </QueryClientProvider>,
    );

    expect(html).toContain('Track movement health across every lane');
    expect(html).toContain('Create a shipment');
    expect(html).toContain('Shipment lifecycle');
    // Labeled field group uses the existing placeholder strings as labels.
    expect(html).toContain('Origin Code');
    expect(html).toContain('Destination Code');
  });

  it('renders the alerts surface with the queue panel and scan action', () => {
    const html = renderToString(
      <QueryClientProvider client={queryClient}>
        <StaticRouter location="/alerts">
          <AlertsPage />
        </StaticRouter>
      </QueryClientProvider>,
    );

    expect(html).toContain('Triage, assign, and close operational risk quickly');
    expect(html).toContain('Create a manual operator alert');
    expect(html).toContain('Alert queue');
    expect(html).toContain('Scan for exceptions');
  });

  it('renders the planning surface with the generate panel and approval board', () => {
    const html = renderToString(
      <QueryClientProvider client={queryClient}>
        <StaticRouter location="/planning">
          <PlanningPage />
        </StaticRouter>
      </QueryClientProvider>,
    );

    expect(html).toContain('Generate and approve replenishment actions');
    expect(html).toContain('Run replenishment planning');
    expect(html).toContain('Horizon (weeks)');
    expect(html).toContain('Approval board');
  });

  it('renders the provider governance surface with keys and the credential form for admins', () => {
    authUserState.user = { role: 'admin', email: 'admin@seedco.com' };
    const html = renderToString(
      <QueryClientProvider client={queryClient}>
        <StaticRouter location="/providers">
          <ProvidersPage />
        </StaticRouter>
      </QueryClientProvider>,
    );
    authUserState.user = null;

    expect(html).toContain('Carrier Integrations');
    expect(html).toContain('Provider Keys');
    expect(html).toContain('Loading keys...');
    expect(html).toContain('Securely Save Key');
  });

  it('renders the unauthorized fallback on the shared dark system without the light card', () => {
    const html = renderToString(
      <StaticRouter location="/unauthorized">
        <UnauthorizedPage />
      </StaticRouter>,
    );

    expect(html).toContain('Unauthorized');
    expect(html).toContain('You do not have permission to access this page.');
    expect(html).not.toContain('bg-white');
  });
});

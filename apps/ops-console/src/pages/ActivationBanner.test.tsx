import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { renderToString } from 'react-dom/server';
import { StaticRouter } from 'react-router';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { ActivationBanner, CapPitchBanner } from '../components/ActivationBanner';
import { dismissPitch, resetWorkspace } from '../services/activationApi';
import type { ActivationState } from '../types/api';

const { apiMock, authMocks } = vi.hoisted(() => ({
  apiMock: { get: vi.fn(), post: vi.fn() },
  authMocks: { logout: vi.fn() },
}));

vi.mock('../services/api', () => ({ api: apiMock }));

vi.mock('../context/AuthContext', () => ({
  useAuth: () => ({ user: { role: 'admin', email: 'a@b.com' }, logout: authMocks.logout }),
}));

function milestone(category: string, label: string, status: 'real' | 'sample' | 'empty', completed: boolean) {
  return {
    category,
    label,
    status,
    real_rows: status === 'real' ? 1 : 0,
    sample_rows: status === 'sample' ? 2 : 0,
    completed,
  };
}

function makeState(overrides: Partial<ActivationState> = {}): ActivationState {
  return {
    organization_id: 'org-1',
    n_of_5: 0,
    pct_complete: 0,
    milestones: [
      milestone('warehouses', 'Warehouses', 'sample', false),
      milestone('items', 'Items', 'sample', false),
      milestone('fleet_assets', 'Fleet Assets', 'sample', false),
      milestone('inventory', 'Inventory', 'sample', false),
      milestone('orders', 'Orders', 'sample', false),
    ],
    m6_completed: false,
    m6_completed_at: null,
    next_step: { category: 'warehouses', label: 'Warehouses', cta: '/upload' },
    banner: { visible: true, n_of_5: 0, pct_complete: 0, cta: '/upload', demo_mode: true },
    free_cap: { locked: false, utilization_pct: 0, message: null },
    pitch: { banner: null, dismissible: false, fired: [] },
    toast_fired: false,
    ...overrides,
  };
}

function renderWithState(state: ActivationState, node: React.ReactNode): string {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  queryClient.setQueryData(['activation'], state);
  return renderToString(
    <QueryClientProvider client={queryClient}>
      <StaticRouter location="/">{node}</StaticRouter>
    </QueryClientProvider>,
  );
}

/** react-dom/server inserts `<!-- -->` at JSX expression boundaries;
 * strip them so copy assertions read as authored text. */
function strip(html: string): string {
  return html.replace(/<!-- -->/g, '');
}

beforeEach(() => {
  apiMock.get.mockReset();
  apiMock.post.mockReset();
  authMocks.logout.mockReset();
});

describe('ActivationBanner compact (dashboard, NB-34 copy matrix)', () => {
  it('renders the 0-of-5 welcome-back copy with /upload CTA', () => {
    const html = renderWithState(makeState(), <ActivationBanner mode="compact" />);
    expect(strip(html)).toContain('data-testid="activation-banner"');
    expect(strip(html)).toContain('You&#x27;re 0% through onboarding');
    expect(strip(html)).toContain('5 steps remaining');
    expect(strip(html)).toContain('Continue setup');
    expect(strip(html)).toContain('href="/upload"');
  });

  it('renders 40% + remaining categories at 2-of-5', () => {
    const state = makeState({
      n_of_5: 2,
      pct_complete: 40,
      next_step: { category: 'fleet_assets', label: 'Fleet Assets', cta: '/upload' },
      milestones: [
        milestone('warehouses', 'Warehouses', 'real', true),
        milestone('items', 'Items', 'real', true),
        milestone('fleet_assets', 'Fleet Assets', 'sample', false),
        milestone('inventory', 'Inventory', 'sample', false),
        milestone('orders', 'Orders', 'sample', false),
      ],
    });
    const html = renderWithState(state, <ActivationBanner mode="compact" />);
    expect(strip(html)).toContain('You&#x27;re 40% through onboarding');
    expect(strip(html)).toContain('3 steps remaining');
    expect(strip(html)).toContain('Fleet Assets, Inventory, Orders');
  });

  it('renders the 80% pre-optimization copy with /routes CTA at 5-of-5', () => {
    const state = makeState({
      n_of_5: 5,
      pct_complete: 80,
      next_step: null,
      banner: { visible: true, n_of_5: 5, pct_complete: 80, cta: '/routes', demo_mode: false },
      milestones: [
        milestone('warehouses', 'Warehouses', 'real', true),
        milestone('items', 'Items', 'real', true),
        milestone('fleet_assets', 'Fleet Assets', 'real', true),
        milestone('inventory', 'Inventory', 'real', true),
        milestone('orders', 'Orders', 'real', true),
      ],
    });
    const html = renderWithState(state, <ActivationBanner mode="compact" />);
    expect(strip(html)).toContain('You&#x27;re 80% through onboarding');
    expect(strip(html)).toContain('run your first route optimization');
    expect(strip(html)).toContain('href="/routes"');
    expect(html).not.toContain('steps remaining');
  });

  it('renders nothing once milestone 6 completes (NB-34.2)', () => {
    const state = makeState({
      m6_completed: true,
      banner: { visible: false, n_of_5: 5, pct_complete: 80, cta: null, demo_mode: false },
    });
    const html = renderWithState(state, <ActivationBanner mode="compact" />);
    expect(html).not.toContain('data-testid="activation-banner"');
  });
});

describe('ActivationBanner checklist (upload page, NB-26 + NB-30.5)', () => {
  it('renders the demo copy with per-category origin chips and progress', () => {
    const state = makeState({
      milestones: [
        milestone('warehouses', 'Warehouses', 'real', true),
        milestone('items', 'Items', 'sample', false),
        milestone('fleet_assets', 'Fleet Assets', 'empty', false),
        milestone('inventory', 'Inventory', 'sample', false),
        milestone('orders', 'Orders', 'sample', false),
      ],
    });
    const html = renderWithState(state, <ActivationBanner mode="checklist" />);
    expect(strip(html)).toContain('data-testid="activation-checklist"');
    expect(strip(html)).toContain('You&#x27;re viewing a demo workspace with sample data');
    expect(strip(html)).toContain('0 of 5 categories is yours');
    expect(html).toContain('data-testid="milestone-chip-warehouses"');
    expect(html).toContain('data-testid="milestone-chip-fleet_assets"');
    expect(strip(html)).toContain('next step');
  });

  it('renders the 80% pre-optimization copy with a /routes CTA at 5-of-5 (decision #8)', () => {
    const state = makeState({
      n_of_5: 5,
      pct_complete: 80,
      next_step: null,
      banner: { visible: true, n_of_5: 5, pct_complete: 80, cta: '/routes', demo_mode: false },
      milestones: [
        milestone('warehouses', 'Warehouses', 'real', true),
        milestone('items', 'Items', 'real', true),
        milestone('fleet_assets', 'Fleet Assets', 'real', true),
        milestone('inventory', 'Inventory', 'real', true),
        milestone('orders', 'Orders', 'real', true),
      ],
    });
    const html = renderWithState(state, <ActivationBanner mode="checklist" />);
    expect(html).toContain('data-testid="activation-checklist"');
    expect(strip(html)).toContain(
      'You&#x27;re 80% through onboarding — run your first route optimization to complete setup.',
    );
    expect(html).toContain('href="/routes"');
    // the demo messaging is absent at 5-of-5 (decision #8)
    expect(strip(html)).not.toContain('viewing a demo workspace');
    expect(strip(html)).not.toContain('categories is yours');
  });
});

describe('CapPitchBanner (every-page slot, NB-31.6 + NB-32)', () => {
  it('renders the p100 hard-lock banner with an /account Upgrade now CTA', () => {
    const state = makeState({
      free_cap: {
        locked: true,
        utilization_pct: 100,
        message: 'Free tier cap reached. Writes resume next month, or upgrade now to continue immediately.',
      },
      pitch: { banner: 'p100', dismissible: false, fired: ['p60', 'p80'] },
    });
    const html = renderWithState(state, <CapPitchBanner />);
    expect(strip(html)).toContain('data-testid="cap-pitch-banner"');
    expect(strip(html)).toContain('Free tier cap reached');
    expect(strip(html)).toContain('Upgrade now');
    expect(strip(html)).toContain('href="/account"');
  });

  it('renders the p80 persistent banner with a See pricing /account CTA and no dismiss', () => {
    const state = makeState({
      free_cap: { locked: false, utilization_pct: 80, message: null },
      pitch: { banner: 'p80', dismissible: false, fired: ['p60', 'p80'] },
    });
    const html = renderWithState(state, <CapPitchBanner />);
    expect(strip(html)).toContain('You&#x27;ve used 80% of your Free tier tasks');
    expect(strip(html)).toContain('See pricing');
    expect(strip(html)).toContain('href="/account"');
    expect(html).not.toContain('Dismiss');
  });

  it('renders the p60 informational banner with a dismiss button and no CTA', () => {
    const state = makeState({
      free_cap: { locked: false, utilization_pct: 60, message: null },
      pitch: { banner: 'p60', dismissible: true, fired: ['p60'] },
    });
    const html = renderWithState(state, <CapPitchBanner />);
    expect(strip(html)).toContain('You&#x27;ve used 60% of your Free tier tasks this month.');
    expect(strip(html)).toContain('Dismiss');
    expect(html).not.toContain('href="/account"');
  });

  it('renders nothing when no pitch is active', () => {
    const html = renderWithState(makeState(), <CapPitchBanner />);
    expect(html).not.toContain('data-testid="cap-pitch-banner"');
  });
});

describe('activationApi service contract', () => {
  it('dismissPitch posts the p60 level to /activation/pitch-dismiss', async () => {
    apiMock.post.mockResolvedValue({ data: { dismissed: true } });
    await dismissPitch('p60');
    expect(apiMock.post).toHaveBeenCalledWith('/activation/pitch-dismiss', { level: 'p60' });
  });

  it('resetWorkspace posts the workspace name to /activation/reset', async () => {
    apiMock.post.mockResolvedValue({ data: { rows_reseeded: { warehouses: 2 }, activation_reset: true } });
    await resetWorkspace('Seed Co');
    expect(apiMock.post).toHaveBeenCalledWith('/activation/reset', { workspace_name: 'Seed Co' });
  });

  it('getActivationState reads /activation', async () => {
    apiMock.get.mockResolvedValue({ data: makeState() });
    const { getActivationState } = await import('../services/activationApi');
    await getActivationState();
    expect(apiMock.get).toHaveBeenCalledWith('/activation');
  });
});

describe('useResetWorkspace (NB-35.7 reset re-login flow)', () => {
  it('clears the query cache, logs out, and redirects to /login on reset success', async () => {
    const assignSpy = vi.fn();
    vi.stubGlobal('window', { location: { assign: assignSpy } });
    apiMock.post.mockResolvedValue({ data: { rows_reseeded: {}, activation_reset: true } });

    const { useResetWorkspace } = await import('../hooks/queries');
    const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
    queryClient.setQueryData(['activation'], makeState());
    queryClient.setQueryData(['routes', 'schedules'], []);

    let captured:
      | { mutateAsync: (name: string) => Promise<unknown> }
      | undefined;
    function CaptureHarness() {
      captured = useResetWorkspace();
      return null;
    }
    renderToString(
      <QueryClientProvider client={queryClient}>
        <StaticRouter location="/account">
          <CaptureHarness />
        </StaticRouter>
      </QueryClientProvider>,
    );

    expect(captured).toBeDefined();
    await captured!.mutateAsync('Seed Co');

    // server call contract
    expect(apiMock.post).toHaveBeenCalledWith('/activation/reset', { workspace_name: 'Seed Co' });
    // NB-35.7: auth state cleared (query cache wiped) + logout cookie-clear
    expect(queryClient.getQueryData(['activation'])).toBeUndefined();
    expect(queryClient.getQueryData(['routes', 'schedules'])).toBeUndefined();
    expect(authMocks.logout).toHaveBeenCalledTimes(1);
    // redirect to the login page; the next login lands on `/` (decision #10)
    expect(assignSpy).toHaveBeenCalledWith('/login');

    vi.unstubAllGlobals();
  });
});

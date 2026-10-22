import type { ReactElement } from 'react';
import { renderToString } from 'react-dom/server';
import { StaticRouter } from 'react-router';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { DriversPage } from './DriversPage';
import { ShipmentsPage } from './ShipmentsPage';

/**
 * Smoke coverage for the driver roster and cash-on-delivery surfaces (NB-86).
 *
 * The console has no DOM test environment (the suite renders through
 * `react-dom/server`), so these assertions cover the first paint — structure,
 * copy and defaults — while `services/driversCashApi.test.ts` pins the wire
 * contract those surfaces depend on.
 */

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

vi.mock('../services/api', async (importOriginal) => {
  const actual = await importOriginal<typeof import('../services/api')>();
  return {
    ...actual,
    api: {
      get: vi.fn(() => Promise.resolve({ data: [] })),
      post: vi.fn(() => Promise.resolve({ data: {} })),
      patch: vi.fn(() => Promise.resolve({ data: {} })),
      delete: vi.fn(() => Promise.resolve({ data: {} })),
    },
  };
});

/** react-dom/server inserts `<!-- -->` at JSX expression boundaries. */
function strip(html: string): string {
  return html.replace(/<!-- -->/g, '');
}

function render(page: ReactElement, location: string): string {
  return strip(renderToString(<StaticRouter location={location}>{page}</StaticRouter>));
}

beforeEach(() => {
  authUserState.user = { role: 'admin', email: 'owner@addisfreight.et' };
});

describe('Fleet & Cash surface (NB-86)', () => {
  it('leads with the two questions the operator actually asks', () => {
    const html = render(<DriversPage />, '/drivers');
    expect(html).toContain('Know who is carrying the load and what cash is coming back');
  });

  it('shows the end-of-day cash position as four tiles', () => {
    const html = render(<DriversPage />, '/drivers');
    expect(html).toContain('Active drivers');
    expect(html).toContain('Cash with drivers');
    expect(html).toContain('Collected, not banked');
    expect(html).toContain('Shortfall');
  });

  it('defaults every money tile to a zero ETB figure rather than a blank', () => {
    const html = render(<DriversPage />, '/drivers');
    expect(html).toContain('0.00 ETB');
    expect(html).toContain('Every collection matches what was expected.');
  });

  it('offers the roster form with phone as the identifying field', () => {
    const html = render(<DriversPage />, '/drivers');
    expect(html).toContain('Add a driver');
    expect(html).toContain('+251911000001');
    expect(html).toContain('Phone number is how a driver is identified day to day');
  });

  it('frames the roster around the morning question', () => {
    const html = render(<DriversPage />, '/drivers');
    expect(html).toContain('Who is on the fleet today');
    expect(html).toContain('Open a driver to see what they are carrying right now');
  });

  it('frames the ledger around the end-of-day close', () => {
    const html = render(<DriversPage />, '/drivers');
    expect(html).toContain('Cash position');
    expect(html).toContain('Every delivery that expects cash at the door');
    expect(html).toContain('Settled to date:');
  });

  it('renders for an operator as well as an admin', () => {
    authUserState.user = { role: 'operator', email: 'dispatch@addisfreight.et' };
    const html = render(<DriversPage />, '/drivers');
    expect(html).toContain('Know who is carrying the load and what cash is coming back');
  });

  it('renders when no user is present at all', () => {
    authUserState.user = null;
    const html = render(<DriversPage />, '/drivers');
    expect(html).toContain('Cash position');
  });
});

describe('Shipments board cash capture (NB-86)', () => {
  it('lets a dispatcher assign a driver and a cash-on-delivery amount at creation', () => {
    const html = render(<ShipmentsPage />, '/shipments');
    expect(html).toContain('Cash on delivery (ETB)');
    expect(html).toContain('Driver');
    expect(html).toContain('Unassigned');
  });

  it('keeps the existing shipment lifecycle controls', () => {
    const html = render(<ShipmentsPage />, '/shipments');
    expect(html).toContain('Track movement health across every lane');
    expect(html).toContain('Shipment lifecycle');
    expect(html).toContain('Create a shipment');
  });
});

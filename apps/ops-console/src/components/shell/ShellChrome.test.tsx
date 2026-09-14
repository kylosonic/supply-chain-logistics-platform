import { renderToString } from 'react-dom/server';
import { StaticRouter } from 'react-router';
import { describe, expect, it } from 'vitest';

import { ShellHeader } from './ShellHeader';
import { ShellSidebar } from './ShellSidebar';
import type { UserRead } from '../../types/auth';

const fixtureUser: UserRead = {
  id: 'user-1',
  username: 'captain',
  email: 'captain@testco.com',
  full_name: 'Captain Test',
  role: 'operator',
  is_active: true,
  created_at: '2026-08-08T00:00:00Z',
};

describe('Shell chrome', () => {
  it('renders the branded navigation groups, routes, codes, and footer identity', () => {
    const html = renderToString(
      <StaticRouter location="/routes">
        <ShellSidebar user={fixtureUser} onLogout={() => undefined} />
      </StaticRouter>,
    );

    expect(html).toContain('FreightPilot');
    expect(html).toContain('Operations workspace');
    expect(html).toContain('Operations');
    expect(html).toContain('Workspace');
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
    expect(html).toContain('Logout');
    expect(html).toContain('captain@testco.com');
    expect(html).toContain('operator');
    expect(html).toContain('aria-current="page"');
  });

  it('renders the shell header context label, descriptor, and identity chips', () => {
    const html = renderToString(
      <ShellHeader
        contextLabel="Control tower"
        descriptor="Routes, exceptions, planning, and workspace governance."
        user={fixtureUser}
        onOpenNavigation={() => undefined}
      />,
    );

    expect(html).toContain('Control tower');
    expect(html).toContain('Routes, exceptions, planning, and workspace governance.');
    expect(html).toContain('operator');
    expect(html).toContain('captain@testco.com');
    expect(html).toContain('Open navigation');
  });
});

import { readFileSync, readdirSync, statSync } from 'node:fs';
import { join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { describe, expect, it } from 'vitest';

/** `apps/ops-console/src` resolved from this test file, independent of cwd. */
const SRC_DIR = fileURLToPath(new URL('.', import.meta.url));

/** This guard file itself contains the patterns as regression literals. */
const SELF = fileURLToPath(import.meta.url);

/** The live-socket hook definition file — the one place `useLiveUpdates(` may live. */
const HOOK_FILE = join(SRC_DIR, 'hooks', 'useLiveUpdates.ts');

function read(rel: string): string {
  return readFileSync(join(SRC_DIR, rel), 'utf8');
}

function sourceFiles(dir: string): string[] {
  const out: string[] = [];
  for (const entry of readdirSync(dir)) {
    const full = join(dir, entry);
    if (statSync(full).isDirectory()) {
      out.push(...sourceFiles(full));
    } else if (/\.(ts|tsx)$/.test(entry) && full !== SELF && full !== HOOK_FILE) {
      out.push(full);
    }
  }
  return out;
}

describe('App route composition guard (TECH-72 / NB-55)', () => {
  const app = read('App.tsx');

  it('mounts Layout exactly once — the single layout route (decision 1)', () => {
    const occurrences = app.split('<Layout').length - 1;
    expect(occurrences).toBe(1);
  });

  it('wraps the Layout route in an auth-only ProtectedRoute (no allowedRoles)', () => {
    expect(app).toMatch(/element={\s*<ProtectedRoute>\s*<Layout \/>\s*<\/ProtectedRoute>\s*}/);
  });

  it('keeps the dashboard as the index route with no role gate', () => {
    expect(app).toContain('<Route index element={<ProtectedRoute><DashboardPage /></ProtectedRoute>} />');
  });

  it('preserves the exact per-route allowedRoles arrays on every console child route', () => {
    expect(app).toContain(
      "<Route path=\"/routes\" element={<ProtectedRoute allowedRoles={['admin', 'operator', 'viewer']}><RoutesPage /></ProtectedRoute>} />",
    );
    expect(app).toContain(
      "<Route path=\"/upload\" element={<ProtectedRoute allowedRoles={['admin', 'operator']}><UploadPage /></ProtectedRoute>} />",
    );
    expect(app).toContain(
      "<Route path=\"/shipments\" element={<ProtectedRoute allowedRoles={['admin', 'operator', 'viewer']}><ShipmentsPage /></ProtectedRoute>} />",
    );
    expect(app).toContain(
      "<Route path=\"/alerts\" element={<ProtectedRoute allowedRoles={['admin', 'operator', 'viewer']}><AlertsPage /></ProtectedRoute>} />",
    );
    expect(app).toContain(
      "<Route path=\"/planning\" element={<ProtectedRoute allowedRoles={['admin', 'operator', 'viewer']}><PlanningPage /></ProtectedRoute>} />",
    );
    expect(app).toContain(
      "<Route path=\"/account\" element={<ProtectedRoute allowedRoles={['admin', 'operator', 'viewer']}><AccountPage /></ProtectedRoute>} />",
    );
    expect(app).toContain(
      "<Route path=\"/providers\" element={<ProtectedRoute allowedRoles={['admin', 'owner', 'operator']}><ProvidersPage /></ProtectedRoute>} />",
    );
    expect(app).toContain(
      "<Route path=\"/receipts\" element={<ProtectedRoute allowedRoles={['admin', 'owner', 'operator', 'viewer']}><ReceiptsPage /></ProtectedRoute>} />",
    );
    expect(app).toContain(
      "<Route path=\"/admin/receipts\" element={<ProtectedRoute allowedRoles={['admin', 'owner']}><AdminReceiptsPage /></ProtectedRoute>} />",
    );
  });

  it('keeps /login, /unauthorized, and the top-level * catch-all outside the layout route', () => {
    expect(app).toContain('<Route path="/login" element={<LoginPage />} />');
    expect(app).toContain('<Route path="/track" element={<TrackingPage />} />');
    expect(app).toContain('<Route path="/unauthorized" element={<UnauthorizedPage />} />');
    expect(app).toContain('<Route path="*" element={<Navigate to="/" replace />} />');
    // The catch-all must be a sibling of the layout route, not a child:
    const layoutRouteIndex = app.indexOf('path="/"');
    const catchAllIndex = app.indexOf('path="*"');
    expect(layoutRouteIndex).toBeGreaterThan(-1);
    expect(catchAllIndex).toBeGreaterThan(layoutRouteIndex);
  });

  it('keeps the top-level Suspense + RouteFallback for the lazy /login and /unauthorized chunks', () => {
    expect(app).toContain('<Suspense fallback={<RouteFallback />}>');
    expect(app).toContain("import { Layout, RouteFallback } from './components/Layout';");
  });
});

describe('Layout shell composition guard (TECH-72 / NB-55)', () => {
  const layout = read('components/Layout.tsx');

  it('renders the page content through <Outlet/>', () => {
    expect(layout).toContain('<Outlet');
  });

  it('nests Suspense around the Outlet with the RouteFallback fallback', () => {
    expect(layout).toContain('<Suspense fallback={<RouteFallback />}>');
  });

  it('exports RouteFallback with the verbatim "Loading workspace surface..." copy', () => {
    expect(layout).toContain('export function RouteFallback()');
    expect(layout).toContain('Loading workspace surface...');
  });

  it('mounts the single SessionLiveUpdates socket owner', () => {
    expect(layout).toContain('<SessionLiveUpdates />');
    expect(layout).toContain("import { SessionLiveUpdates } from './shell/SessionLiveUpdates';");
  });

  it('no longer takes a children prop', () => {
    expect(layout).not.toContain('PropsWithChildren');
    expect(layout).not.toContain('children');
  });
});

describe('single live connection guard (TECH-73 / NB-56)', () => {
  it('DashboardPage no longer owns a socket', () => {
    expect(read('pages/DashboardPage.tsx')).not.toContain('useLiveUpdates(');
  });

  it('RoutesPage no longer owns a socket', () => {
    expect(read('pages/RoutesPage.tsx')).not.toContain('useLiveUpdates(');
  });

  it('useLiveUpdates( occurs exactly once across src outside the hook definition (the shell owns it)', () => {
    const owners: string[] = [];
    let total = 0;
    for (const file of sourceFiles(SRC_DIR)) {
      const content = readFileSync(file, 'utf8');
      const count = content.split('useLiveUpdates(').length - 1;
      total += count;
      if (count > 0) owners.push(file);
    }
    expect(total).toBe(1);
    expect(owners).toEqual([join(SRC_DIR, 'components', 'shell', 'SessionLiveUpdates.tsx')]);
  });
});

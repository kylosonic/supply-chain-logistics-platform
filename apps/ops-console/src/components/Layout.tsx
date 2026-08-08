import { Suspense, useState } from 'react';
import { Outlet } from 'react-router-dom';

import { useAuth } from '../context/AuthContext';
import { CapPitchBanner } from './ActivationBanner';
import { SessionLiveUpdates } from './shell/SessionLiveUpdates';
import { ShellHeader } from './shell/ShellHeader';
import { ShellSidebar } from './shell/ShellSidebar';

const SHELL_CONTEXT_LABEL = 'Control tower';
const SHELL_DESCRIPTOR = 'Routes, exceptions, planning, and workspace governance.';

/** Lazy-chunk fallback rendered INSIDE the shell so the layout stays mounted
 *  while a page chunk loads (TECH-72). Also reused by App.tsx at the top
 *  level for the /login and /unauthorized lazy chunks. */
export function RouteFallback() {
  return (
    <div className="fp-nested-surface px-5 py-5 text-sm text-slate-400">
      Loading workspace surface...
    </div>
  );
}

export function Layout() {
  const { user, logout } = useAuth();
  const [sidebarOpen, setSidebarOpen] = useState(false);

  return (
    <div className="min-h-screen bg-[var(--fp-black)] text-slate-100">
      <SessionLiveUpdates />
      <div className="mx-auto flex max-w-[1520px] gap-5 px-4 py-4 lg:gap-6 lg:px-6">
        <aside className="hidden w-[280px] shrink-0 lg:block">
          <div className="sticky top-4 flex h-[calc(100vh-2rem)] flex-col">
            <ShellSidebar user={user} onLogout={logout} />
          </div>
        </aside>

        {sidebarOpen ? (
          <div className="fixed inset-0 z-50 lg:hidden">
            <div className="absolute inset-0 bg-slate-950/80" onClick={() => setSidebarOpen(false)} />
            <aside className="absolute inset-y-0 left-0 w-[320px] overflow-y-auto border-r border-slate-800/70 bg-[var(--fp-black)] p-4">
              <ShellSidebar user={user} onLogout={logout} onNavigate={() => setSidebarOpen(false)} />
            </aside>
          </div>
        ) : null}

        <div className="min-w-0 flex-1 space-y-5">
          <ShellHeader
            contextLabel={SHELL_CONTEXT_LABEL}
            descriptor={SHELL_DESCRIPTOR}
            user={user}
            onOpenNavigation={() => setSidebarOpen(true)}
          />
          <CapPitchBanner />
          <main className="space-y-5">
            <Suspense fallback={<RouteFallback />}>
              <Outlet />
            </Suspense>
          </main>
        </div>
      </div>
    </div>
  );
}

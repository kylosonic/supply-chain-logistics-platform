import { useState } from 'react';
import { Link, NavLink } from 'react-router-dom';
import type { PropsWithChildren } from 'react';

import { useAuth } from '../context/AuthContext';
import { CapPitchBanner } from './ActivationBanner';

const navGroups = [
  {
    label: 'Operations',
    items: [
      { to: '/', label: 'Control Tower', code: 'CT' },
      { to: '/routes', label: 'Route Studio', code: 'RT' },
      { to: '/shipments', label: 'Shipments', code: 'SH' },
      { to: '/alerts', label: 'Exceptions', code: 'EX' },
      { to: '/planning', label: 'Planning', code: 'PL' },
    ],
  },
  {
    label: 'Workspace',
    items: [
      { to: '/upload', label: 'Data Intake', code: 'DI' },
      { to: '/receipts', label: 'Payments', code: 'PY' },
      { to: '/admin/receipts', label: 'Verification Queue', code: 'VQ' },
      { to: '/account', label: 'Workspace', code: 'WS' },
      { to: '/providers', label: 'Integrations', code: 'IN' },
    ],
  },
];

function NavItem({
  to,
  code,
  label,
  onNavigate,
}: {
  to: string;
  code: string;
  label: string;
  onNavigate?: () => void;
}) {
  return (
    <NavLink
      to={to}
      end={to === '/'}
      onClick={onNavigate}
      className={({ isActive }) =>
        `grid grid-cols-[40px_minmax(0,1fr)] items-center gap-3 rounded-xl border px-3 py-2.5 text-sm transition-colors ${
          isActive
            ? 'border-sky-400/30 bg-slate-800/65 text-slate-100'
            : 'border-transparent text-slate-400 hover:bg-slate-800/45 hover:text-slate-200'
        }`
      }
    >
      {({ isActive }) => (
        <>
          <span
            className={`inline-grid h-8 w-8 place-items-center rounded-lg border text-[11px] font-medium ${
              isActive
                ? 'border-sky-400/25 bg-sky-500/10 text-sky-300'
                : 'border-slate-800/60 bg-slate-900/60 text-slate-500'
            }`}
          >
            {code}
          </span>
          <span className="truncate">{label}</span>
        </>
      )}
    </NavLink>
  );
}

function SidebarContent({ onNavigate }: { onNavigate?: () => void }) {
  const { user, logout } = useAuth();

  return (
    <div className="flex h-full flex-col gap-4">
      <div className="rounded-2xl border border-slate-800/60 bg-slate-900/35 px-4 py-4">
        <Link to="/" className="group inline-flex items-center gap-3 no-underline" onClick={onNavigate}>
          <span className="inline-grid h-10 w-10 place-items-center rounded-lg bg-sky-500 font-['Space_Grotesk'] text-sm font-bold text-slate-950">
            FP
          </span>
          <span className="grid gap-0.5">
            <strong className="font-['Space_Grotesk'] text-base font-semibold tracking-tight text-slate-100">
              FreightPilot
            </strong>
            <span className="text-xs text-slate-500">Operations workspace</span>
          </span>
        </Link>
      </div>

      <nav className="flex-1 overflow-y-auto" aria-label="Workspace views">
        <div className="space-y-4">
          {navGroups.map((group) => (
            <section key={group.label} className="space-y-2">
              <p className="px-2 text-[11px] font-medium uppercase tracking-wide text-slate-500">{group.label}</p>
              <div className="grid gap-1">
                {group.items.map((item) => (
                  <NavItem key={item.to} {...item} onNavigate={onNavigate} />
                ))}
              </div>
            </section>
          ))}
        </div>
      </nav>

      <div className="rounded-2xl border border-slate-800/60 bg-slate-900/35 px-4 py-4">
        <div className="space-y-1">
          <p className="text-xs font-medium uppercase tracking-wide text-slate-500">Signed in</p>
          <p className="truncate text-sm font-medium capitalize text-slate-200">{user?.role || 'viewer'}</p>
          <p className="truncate text-xs text-slate-500">{user?.email || user?.username}</p>
        </div>
        <button
          onClick={logout}
          className="mt-4 w-full rounded-lg border border-slate-700/60 px-3 py-2 text-sm font-medium text-slate-300 transition-colors hover:border-slate-500 hover:bg-slate-800/50"
        >
          Logout
        </button>
      </div>
    </div>
  );
}

export function Layout({ children }: PropsWithChildren) {
  const { user } = useAuth();
  const [sidebarOpen, setSidebarOpen] = useState(false);

  return (
    <div className="min-h-screen text-slate-100">
      <div className="mx-auto flex max-w-[1520px] gap-6 px-4 py-4 lg:px-6">
        <aside className="hidden w-[260px] shrink-0 lg:block">
          <div className="sticky top-4 flex h-[calc(100vh-2rem)] flex-col">
            <SidebarContent />
          </div>
        </aside>

        {sidebarOpen ? (
          <div className="fixed inset-0 z-50 lg:hidden">
            <div className="absolute inset-0 bg-slate-950/70" onClick={() => setSidebarOpen(false)} />
            <aside className="absolute inset-y-0 left-0 w-[300px] overflow-y-auto border-r border-slate-800/60 bg-[#0a0f16] p-4">
              <SidebarContent onNavigate={() => setSidebarOpen(false)} />
            </aside>
          </div>
        ) : null}

        <div className="min-w-0 flex-1">
          <header className="mb-6 rounded-2xl border border-slate-800/60 bg-slate-900/35 px-4 py-4 lg:px-5">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div className="flex items-center gap-3">
                <button
                  onClick={() => setSidebarOpen(true)}
                  className="inline-grid h-9 w-9 place-items-center rounded-lg border border-slate-700/60 bg-slate-900 lg:hidden"
                  aria-label="Open navigation"
                >
                  <svg className="h-4 w-4 text-slate-300" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M4 6h16M4 12h16M4 18h16" />
                  </svg>
                </button>
                <div>
                  <p className="text-xs font-medium uppercase tracking-wide text-slate-500">Control tower</p>
                  <p className="text-sm text-slate-300">Routes, exceptions, planning, and workspace governance.</p>
                </div>
              </div>

              <div className="flex flex-wrap items-center gap-2 text-xs text-slate-400">
                <span className="rounded-md border border-slate-700/60 bg-slate-900 px-2.5 py-1 font-mono uppercase tracking-wide text-slate-300">
                  {user?.role}
                </span>
                <span className="rounded-md border border-slate-700/60 bg-slate-900 px-2.5 py-1 text-slate-400">
                  {user?.email || user?.username}
                </span>
              </div>
            </div>
          </header>

          <CapPitchBanner />

          <main className="space-y-5">{children}</main>
        </div>
      </div>
    </div>
  );
}

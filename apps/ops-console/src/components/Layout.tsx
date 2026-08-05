import { useState } from 'react';
import { Link, NavLink } from 'react-router-dom';
import type { PropsWithChildren } from 'react';

import { useAuth } from '../context/AuthContext';

const navItems = [
  { to: '/', label: 'Control Tower', code: 'CT', hint: 'Operations overview' },
  { to: '/routes', label: 'Route Studio', code: 'RT', hint: 'Optimize and dispatch' },
  { to: '/shipments', label: 'Shipments', code: 'SH', hint: 'Movement lifecycle' },
  { to: '/alerts', label: 'Exceptions', code: 'EX', hint: 'Triage and response' },
  { to: '/planning', label: 'Planning', code: 'PL', hint: 'Replenishment rhythm' },
  { to: '/upload', label: 'Data Intake', code: 'DI', hint: 'CSV onboarding' },
  { to: '/receipts', label: 'Payments', code: 'PY', hint: 'Receipts and wallet' },
  { to: '/admin/receipts', label: 'Verification Queue', code: 'VQ', hint: 'Receipt verdicts' },
  { to: '/account', label: 'Workspace', code: 'WS', hint: 'Billing and AI keys' },
  { to: '/providers', label: 'Integrations', code: 'IN', hint: 'Carrier API keys' },
];

function SidebarContent({ onNavigate }: { onNavigate?: () => void }) {
  const { user, logout } = useAuth();

  return (
    <div className="flex h-full flex-col gap-4">
      <div className="top-highlight rounded-[30px] border border-slate-800/80 bg-slate-950/82 p-5 shadow-[0_24px_80px_rgba(2,12,20,0.34)] backdrop-blur">
        <Link to="/" className="group inline-flex items-start gap-4 no-underline" onClick={onNavigate}>
          <span className="inline-grid h-12 w-12 place-items-center rounded-2xl bg-gradient-to-br from-sky-300 via-sky-400 to-teal-300 font-['Space_Grotesk'] text-sm font-semibold text-slate-950 transition group-hover:shadow-[0_0_24px_rgba(56,189,248,0.3)]">
            FP
          </span>
          <span className="grid gap-1">
            <strong className="font-['Space_Grotesk'] text-lg font-semibold text-slate-50">FreightPilot</strong>
            <span className="text-sm leading-6 text-slate-400">Route, exception, and governance control layer.</span>
          </span>
        </Link>
      </div>

      <nav className="flex-1 overflow-y-auto rounded-[30px] border border-slate-800/80 bg-slate-950/78 p-3 shadow-[0_24px_80px_rgba(2,12,20,0.3)] backdrop-blur">
        <div className="mb-3 px-3 pt-2 text-xs font-semibold uppercase tracking-[0.24em] text-sky-300/70">
          Workspace views
        </div>
        <div className="grid gap-2">
          {navItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.to === '/'}
              onClick={onNavigate}
              className={({ isActive }) =>
                `grid grid-cols-[44px_minmax(0,1fr)] items-center gap-3 rounded-[22px] border px-3 py-3 transition-all duration-200 ${
                  isActive
                    ? 'border-sky-400/30 bg-sky-500/12 text-slate-50 shadow-[0_12px_36px_rgba(14,165,233,0.12)]'
                    : 'border-transparent bg-transparent text-slate-300 hover:border-slate-800/80 hover:bg-slate-900/70'
                }`
              }
            >
              {({ isActive }) => (
                <>
                  <span className={`inline-grid h-11 w-11 place-items-center rounded-2xl text-[11px] font-semibold uppercase tracking-[0.18em] transition-colors ${isActive ? 'bg-sky-500/20 text-sky-200' : 'bg-slate-900 text-slate-200'}`}>
                    {item.code}
                  </span>
                  <span className="grid">
                    <span className="text-sm font-semibold">{item.label}</span>
                    <span className="text-xs text-slate-500">{item.hint}</span>
                  </span>
                </>
              )}
            </NavLink>
          ))}
        </div>
      </nav>

      <div className="grid gap-4">
        <div className="rounded-[26px] border border-slate-800/80 bg-slate-950/72 p-5 shadow-[0_18px_48px_rgba(2,12,20,0.24)]">
          <p className="text-xs font-semibold uppercase tracking-[0.22em] text-slate-500">Operator mode</p>
          <p className="mt-3 font-['Space_Grotesk'] text-xl font-semibold capitalize text-slate-50">{user?.role || 'viewer'}</p>
          <p className="mt-2 text-sm leading-6 text-slate-400">Role-aware routing, approvals, and AI preference controls.</p>
        </div>
        <div className="rounded-[26px] border border-slate-800/80 bg-slate-950/72 p-5 shadow-[0_18px_48px_rgba(2,12,20,0.24)]">
          <p className="text-xs font-semibold uppercase tracking-[0.22em] text-slate-500">Signed in</p>
          <p className="mt-3 break-all text-sm text-slate-200">{user?.email || user?.username}</p>
          <button
            onClick={logout}
            className="glow-ring mt-4 inline-flex min-h-10 items-center justify-center rounded-full border border-slate-700 px-4 text-sm font-semibold text-slate-200 transition hover:border-slate-500 hover:bg-slate-900"
          >
            Logout
          </button>
        </div>
      </div>
    </div>
  );
}

export function Layout({ children }: PropsWithChildren) {
  const { user } = useAuth();
  const [sidebarOpen, setSidebarOpen] = useState(false);

  return (
    <div className="min-h-screen text-slate-100">
      <div className="mx-auto flex max-w-[1520px] gap-5 px-4 py-4 lg:px-6">
        {/* Desktop sidebar */}
        <aside className="hidden w-[310px] shrink-0 lg:block">
          <div className="sticky top-4 flex h-[calc(100vh-2rem)] flex-col">
            <SidebarContent />
          </div>
        </aside>

        {/* Mobile sidebar overlay */}
        {sidebarOpen ? (
          <div className="fixed inset-0 z-50 lg:hidden">
            <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" onClick={() => setSidebarOpen(false)} />
            <aside className="absolute inset-y-0 left-0 w-[310px] overflow-y-auto p-4">
              <SidebarContent onNavigate={() => setSidebarOpen(false)} />
            </aside>
          </div>
        ) : null}

        <div className="min-w-0 flex-1">
          <header className="mb-5 rounded-[30px] border border-slate-800/80 bg-slate-950/72 px-4 py-4 shadow-[0_24px_80px_rgba(2,12,20,0.32)] backdrop-blur lg:px-5">
            <div className="flex flex-wrap items-center justify-between gap-4">
              <div className="space-y-1">
                <div className="inline-flex items-center gap-3">
                  <button
                    onClick={() => setSidebarOpen(true)}
                    className="inline-grid h-10 w-10 place-items-center rounded-xl border border-slate-700 bg-slate-900 lg:hidden"
                    aria-label="Open navigation"
                  >
                    <svg className="h-5 w-5 text-slate-300" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M4 6h16M4 12h16M4 18h16" />
                    </svg>
                  </button>
                  <span className="inline-grid h-10 w-10 place-items-center rounded-2xl bg-gradient-to-br from-sky-300 via-sky-400 to-teal-300 font-['Space_Grotesk'] text-xs font-semibold text-slate-950 lg:hidden">
                    FP
                  </span>
                  <strong className="font-['Space_Grotesk'] text-lg font-semibold text-slate-50 lg:hidden">FreightPilot</strong>
                </div>
                <p className="text-xs font-semibold uppercase tracking-[0.22em] text-sky-300/75">Operations workspace</p>
                <p className="text-sm text-slate-400">Routes, alerts, shipments, planning, and rollout readiness in one surface.</p>
              </div>

              <div className="flex flex-wrap items-center gap-2 text-xs text-slate-400">
                <span className="rounded-full border border-slate-800 bg-slate-900/80 px-3 py-1.5 uppercase tracking-[0.18em] text-slate-300">
                  {user?.role}
                </span>
                <span className="rounded-full border border-slate-800 bg-slate-900/80 px-3 py-1.5">{user?.email || user?.username}</span>
              </div>
            </div>

            <nav className="mt-4 flex gap-2 overflow-x-auto pb-1 lg:hidden">
              {navItems.map((item) => (
                <NavLink
                  key={item.to}
                  to={item.to}
                  end={item.to === '/'}
                  className={({ isActive }) =>
                    `flex items-center gap-1.5 whitespace-nowrap rounded-full border px-3 py-2 text-xs font-semibold transition ${
                      isActive
                        ? 'border-sky-400/40 bg-sky-500/12 text-slate-50'
                        : 'border-slate-800 bg-slate-900/80 text-slate-300'
                    }`
                  }
                >
                  <span className="uppercase tracking-[0.18em]">{item.code}</span>
                  <span className="hidden sm:inline">{item.label}</span>
                </NavLink>
              ))}
            </nav>
          </header>

          <main className="space-y-5">{children}</main>
        </div>
      </div>
    </div>
  );
}

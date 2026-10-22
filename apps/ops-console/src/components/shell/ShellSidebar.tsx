import { Link, NavLink } from 'react-router-dom';

import type { UserRead } from '../../types/auth';

type ShellSidebarProps = {
  user: UserRead | null | undefined;
  onLogout: () => void | Promise<void>;
  onNavigate?: () => void;
};

const navGroups = [
  {
    label: 'Operations',
    items: [
      { to: '/', label: 'Control Tower', code: 'CT' },
      { to: '/routes', label: 'Route Studio', code: 'RT' },
      { to: '/dispatch', label: 'Customer Dispatch', code: 'DP' },
      { to: '/shipments', label: 'Shipments', code: 'SH' },
      { to: '/drivers', label: 'Fleet & Cash', code: 'FC' },
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
] as const;

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
        `grid grid-cols-[44px_minmax(0,1fr)] items-center gap-3 border px-3 py-3 text-sm transition-colors ${
          isActive
            ? 'rounded-[var(--fp-radius-panel)] border-sky-400/35 bg-slate-900/95 text-slate-50'
            : 'rounded-[var(--fp-radius-panel)] border-transparent text-slate-400 hover:border-slate-800/80 hover:bg-slate-900/70 hover:text-slate-200'
        }`
      }
    >
      {({ isActive }) => (
        <>
          <span
            className={`inline-grid h-9 w-9 place-items-center border text-[11px] font-semibold tracking-[0.18em] ${
              isActive
                ? 'rounded-[var(--fp-radius-panel)] border-sky-400/30 bg-sky-500/10 text-sky-200'
                : 'rounded-[var(--fp-radius-panel)] border-slate-800/80 bg-slate-950/80 text-slate-500'
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

export function ShellSidebar({ user, onLogout, onNavigate }: ShellSidebarProps) {
  return (
    <div className="flex h-full flex-col gap-4">
      <div className="fp-shell-surface px-4 py-4 sm:px-5">
        <Link to="/" className="group inline-flex items-center gap-3 no-underline" onClick={onNavigate}>
          <span className="inline-grid h-11 w-11 place-items-center rounded-[var(--fp-radius-panel)] bg-sky-500 font-['Space_Grotesk'] text-sm font-bold text-slate-950">
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

      <nav className="fp-shell-surface flex-1 overflow-y-auto px-3 py-4 sm:px-4" aria-label="Workspace views">
        <div className="space-y-5">
          {navGroups.map((group) => (
            <section key={group.label} className="space-y-2.5">
              <p className="px-2 text-[11px] font-medium tracking-[0.18em] text-slate-500">{group.label}</p>
              <div className="grid gap-1.5">
                {group.items.map((item) => (
                  <NavItem key={item.to} {...item} onNavigate={onNavigate} />
                ))}
              </div>
            </section>
          ))}
        </div>
      </nav>

      <div className="fp-shell-surface px-4 py-4 sm:px-5">
        <div className="space-y-1">
          <p className="text-xs font-medium tracking-[0.18em] text-slate-500">Signed in</p>
          <p className="truncate text-sm font-medium capitalize text-slate-100">{user?.role || 'viewer'}</p>
          <p className="truncate text-xs text-slate-500">{user?.email || user?.username}</p>
        </div>
        <button
          type="button"
          onClick={onLogout}
          className="mt-4 w-full rounded-[var(--fp-radius-panel)] border border-slate-700/70 bg-slate-950/70 px-3 py-2.5 text-sm font-medium text-slate-300 transition-colors hover:border-slate-500/80 hover:bg-slate-900/80 hover:text-slate-100"
        >
          Logout
        </button>
      </div>
    </div>
  );
}

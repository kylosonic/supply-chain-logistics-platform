import { Link, NavLink } from 'react-router-dom';
import type { PropsWithChildren } from 'react';

import { useAuth } from '../context/AuthContext';

const navItems = [
  { to: '/', label: 'Dashboard' },
  { to: '/routes', label: 'Routes' },
  { to: '/shipments', label: 'Shipments' },
  { to: '/alerts', label: 'Alerts' },
  { to: '/planning', label: 'Planning' },
  { to: '/upload', label: 'CSV Upload' },
  { to: '/account', label: 'Account' },
];

export function Layout({ children }: PropsWithChildren) {
  const { user, logout } = useAuth();

  return (
    <div className="min-h-screen bg-slate-100">
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-4 py-4 sm:px-6 lg:px-8">
          <Link to="/" className="text-lg font-semibold text-slate-900">
            Supply Chain Logistics Platform
          </Link>
          <div className="flex items-center gap-4">
            <nav className="flex gap-2">
              {navItems.map((item) => (
                <NavLink
                  key={item.to}
                  to={item.to}
                  className={({ isActive }) =>
                    `rounded-md px-3 py-2 text-sm font-medium ${
                      isActive ? 'bg-slate-900 text-white' : 'text-slate-700 hover:bg-slate-200'
                    }`
                  }
                >
                  {item.label}
                </NavLink>
              ))}
            </nav>
            <div className="flex items-center gap-2 text-xs text-slate-600">
              <span>{user?.email || user?.username}</span>
              <span className="rounded bg-slate-100 px-2 py-1">{user?.role}</span>
              <button onClick={logout} className="rounded border border-slate-300 px-2 py-1 hover:bg-slate-100">
                Logout
              </button>
            </div>
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-7xl px-4 py-6 sm:px-6 lg:px-8">{children}</main>
    </div>
  );
}

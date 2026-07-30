import { useState } from 'react';
import { Navigate } from 'react-router-dom';

import { useAuth } from '../context/AuthContext';
import { register as registerApi } from '../services/authApi';

function getErrorMessage(err: unknown, fallback: string): string {
  if (typeof err === 'object' && err !== null && 'response' in err) {
    const response = (err as { response?: { data?: { detail?: string } } }).response;
    if (response?.data?.detail) {
      return response.data.detail;
    }
  }
  if (err instanceof Error && err.message) {
    return err.message;
  }
  return fallback;
}

export function LoginPage() {
  const { login, isAuthenticated } = useAuth();
  const signupUrl = import.meta.env.VITE_SIGNUP_URL || 'http://localhost:8081#signup';
  const [identifier, setIdentifier] = useState('admin@testco.com');
  const [password, setPassword] = useState('admin12345');
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isBootstrapping, setIsBootstrapping] = useState(false);

  if (isAuthenticated) {
    return <Navigate to="/" replace />;
  }

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setIsSubmitting(true);
    try {
      await login(identifier, password);
    } catch (err: unknown) {
      setError(getErrorMessage(err, 'Login failed'));
    } finally {
      setIsSubmitting(false);
    }
  }

  async function onBootstrapInitialAdmin() {
    setError(null);
    setIsBootstrapping(true);
    try {
      await registerApi(identifier, password, 'admin');
      await login(identifier, password);
    } catch (err: unknown) {
      setError(getErrorMessage(err, 'Failed to create initial admin'));
    } finally {
      setIsBootstrapping(false);
    }
  }

  return (
    <div className="mx-auto grid min-h-screen w-full max-w-[1400px] items-center gap-6 px-4 py-8 lg:grid-cols-[1.05fr_0.95fr] lg:px-6">
      <section className="animate-slide-up top-highlight overflow-hidden rounded-[34px] border border-slate-800/80 bg-[radial-gradient(circle_at_top_left,_rgba(56,189,248,0.18),_transparent_24%),linear-gradient(160deg,rgba(6,14,21,0.96),rgba(11,29,40,0.92))] p-8 shadow-[0_28px_90px_rgba(2,12,20,0.4)]">
        <div className="max-w-2xl space-y-5">
          <p className="text-xs font-semibold uppercase tracking-[0.24em] text-sky-300/80">FreightPilot workspace</p>
          <h1 className="font-['Space_Grotesk'] text-[clamp(2.5rem,4vw,4.2rem)] font-semibold leading-none text-slate-50">
            Operator access to routes, exceptions, launch readiness, and billing control.
          </h1>
          <p className="max-w-2xl text-sm leading-7 text-slate-300">
            Sign in with your company credentials to enter the command tower. If your workspace is new, create the
            company account from the product site first and return here for live operations.
          </p>

          <div className="grid gap-4 sm:grid-cols-3">
            {[
              { eyebrow: 'Routes', title: 'Optimize', detail: 'Model route decisions with cost and schedule context visible.' },
              { eyebrow: 'Exceptions', title: 'Respond', detail: 'Triage alerts and delayed shipments before they age into cost.' },
              { eyebrow: 'Workspace', title: 'Govern', detail: 'Manage billing tiers, AI provider keys, and launch readiness signals.' },
            ].map((card) => (
              <article key={card.eyebrow} className="hover-lift rounded-[24px] border border-slate-800 bg-slate-950/55 p-4 transition">
                <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">{card.eyebrow}</p>
                <p className="mt-3 font-['Space_Grotesk'] text-xl font-semibold text-slate-50">{card.title}</p>
                <p className="mt-2 text-sm leading-6 text-slate-400">{card.detail}</p>
              </article>
            ))}
          </div>
        </div>
      </section>

      <section className="animate-slide-up overflow-hidden rounded-[34px] border border-slate-800/80 bg-slate-950/76 p-8 shadow-[0_24px_80px_rgba(2,12,20,0.36)] backdrop-blur" style={{ animationDelay: '0.1s' }}>
        <div className="space-y-6">
          <div className="space-y-2">
            <p className="text-xs font-semibold uppercase tracking-[0.24em] text-sky-300/80">Control tower login</p>
            <h2 className="font-['Space_Grotesk'] text-3xl font-semibold text-slate-50">Sign in to your workspace</h2>
            <p className="text-sm leading-6 text-slate-400">Use your company email or username. Demo credentials remain prefilled for local validation.</p>
          </div>

          <form className="space-y-4" onSubmit={onSubmit}>
            <label className="grid gap-2 text-sm text-slate-300">
              Company email or username
              <input
                className="glow-ring min-h-12 rounded-2xl border border-slate-700 bg-slate-900/80 px-4 text-slate-100 outline-none transition focus:border-sky-400/50"
                placeholder="Company email or username"
                value={identifier}
                onChange={(e) => setIdentifier(e.target.value)}
              />
            </label>
            <label className="grid gap-2 text-sm text-slate-300">
              Password
              <input
                className="glow-ring min-h-12 rounded-2xl border border-slate-700 bg-slate-900/80 px-4 text-slate-100 outline-none transition focus:border-sky-400/50"
                placeholder="Password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
              />
            </label>

            <div className="grid gap-3 pt-2">
              <button
                disabled={isSubmitting}
                className="glow-ring inline-flex min-h-12 items-center justify-center gap-2 rounded-full bg-gradient-to-r from-sky-300 via-sky-400 to-teal-300 px-4 text-sm font-semibold text-slate-950 transition hover:brightness-105 disabled:cursor-not-allowed disabled:opacity-60"
              >
                {isSubmitting ? (
                  <svg className="animate-spin-slow h-4 w-4" viewBox="0 0 24 24" fill="none"><circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeDasharray="50 20" /></svg>
                ) : null}
                {isSubmitting ? 'Signing in...' : 'Enter control tower'}
              </button>
              <button
                type="button"
                disabled={isBootstrapping}
                onClick={onBootstrapInitialAdmin}
                className="glow-ring inline-flex min-h-12 items-center justify-center gap-2 rounded-full border border-slate-700 px-4 text-sm font-semibold text-slate-200 transition hover:border-slate-500 hover:bg-slate-900 disabled:cursor-not-allowed disabled:opacity-60"
              >
                {isBootstrapping ? (
                  <svg className="animate-spin-slow h-4 w-4" viewBox="0 0 24 24" fill="none"><circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeDasharray="50 20" /></svg>
                ) : null}
                {isBootstrapping ? 'Creating admin...' : 'Create initial admin'}
              </button>
            </div>
          </form>

          {error ? (
            <div className="animate-fade-in rounded-2xl border border-rose-500/25 bg-rose-950/18 px-4 py-3 text-sm text-rose-200">{error}</div>
          ) : null}

          <div className="rounded-[24px] border border-slate-800 bg-slate-900/60 p-4 text-sm leading-6 text-slate-400">
            <p>New workspace?</p>
            <p className="mt-2">Create the company account on the product site, choose your tier, then return here to continue in the desktop or web control tower.</p>
            <a href={signupUrl} className="mt-3 inline-flex font-semibold text-sky-300 no-underline transition hover:text-sky-200" target="_blank" rel="noreferrer">
              Create company account →
            </a>
          </div>
        </div>
      </section>
    </div>
  );
}

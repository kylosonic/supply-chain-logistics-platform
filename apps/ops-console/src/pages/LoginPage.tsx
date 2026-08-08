import { useState } from 'react';
import { Navigate } from 'react-router-dom';

import { useAuth } from '../context/AuthContext';
import { register as registerApi } from '../services/authApi';
import { bootstrapErrorMessage } from '../services/authErrors';

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

const VALUE_POINTS = [
  {
    label: 'Routes',
    title: 'Model dispatch decisions before they cost money.',
  },
  {
    label: 'Exceptions',
    title: 'Keep operational risks visible and actionable.',
  },
  {
    label: 'Workspace',
    title: 'Control billing, AI providers, and launch readiness in one place.',
  },
];

export function LoginPage() {
  const { login, isAuthenticated } = useAuth();
  const signupUrl = import.meta.env.VITE_SIGNUP_URL || 'http://localhost:8081#signup';
  const [identifier, setIdentifier] = useState(() =>
    import.meta.env.PROD ? '' : 'admin@testco.com',
  );
  const [password, setPassword] = useState(() => (import.meta.env.PROD ? '' : 'admin12345'));
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
      setError(bootstrapErrorMessage(err, 'Failed to create initial admin'));
    } finally {
      setIsBootstrapping(false);
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center px-4 py-8 lg:px-6">
      <div className="grid w-full max-w-5xl gap-6 lg:grid-cols-[1.02fr_0.98fr]">
        <section className="rounded-2xl border border-slate-800/60 bg-slate-900/35 px-6 py-7 sm:px-8 sm:py-8">
          <div className="max-w-xl space-y-6">
            <div className="space-y-3">
              <span className="inline-grid h-11 w-11 place-items-center rounded-lg bg-sky-500 font-['Space_Grotesk'] text-sm font-bold text-slate-950">
                FP
              </span>
              <div className="space-y-1.5">
                <p className="text-xs font-medium uppercase tracking-wide text-slate-500">FreightPilot workspace</p>
                <h1 className="font-['Space_Grotesk'] text-[clamp(2rem,3.2vw,2.8rem)] font-semibold leading-tight tracking-tight text-slate-100">
                  Enter the control tower with the same calm surface you saw on the site.
                </h1>
                <p className="max-w-[34rem] text-sm leading-7 text-slate-400">
                  Sign in with the company account you created during launch. Once inside, your routes,
                  exceptions, onboarding progress, and provider controls all live in one operator surface.
                </p>
              </div>
            </div>

            <div className="grid gap-3 sm:grid-cols-3 lg:grid-cols-1 xl:grid-cols-3">
              {VALUE_POINTS.map((point) => (
                <article key={point.label} className="rounded-xl border border-slate-800/60 bg-slate-900/40 px-4 py-4">
                  <p className="text-[11px] font-medium uppercase tracking-wide text-slate-500">{point.label}</p>
                  <p className="mt-2 text-sm leading-6 text-slate-200">{point.title}</p>
                </article>
              ))}
            </div>
          </div>
        </section>

        <section className="rounded-2xl border border-slate-800/60 bg-slate-900/35 px-6 py-7 sm:px-8 sm:py-8">
          <div className="space-y-6">
            <div className="space-y-1.5">
              <p className="text-xs font-medium uppercase tracking-wide text-slate-500">Control tower login</p>
              <h2 className="font-['Space_Grotesk'] text-2xl font-semibold tracking-tight text-slate-100">
                Sign in to your workspace
              </h2>
              <p className="text-sm leading-6 text-slate-400">
                Use the company email and password you used when you created the workspace.
              </p>
            </div>

            <form className="space-y-4" onSubmit={onSubmit}>
              <div className="space-y-1.5">
                <label htmlFor="identifier" className="block text-sm font-medium text-slate-300">
                  Company email or username
                </label>
                <input
                  id="identifier"
                  className="w-full rounded-lg border border-slate-700/60 bg-slate-900 px-3.5 py-2.5 text-sm text-slate-100 outline-none transition-colors focus:border-sky-500/60"
                  placeholder="you@company.com"
                  value={identifier}
                  onChange={(e) => setIdentifier(e.target.value)}
                  autoComplete="username"
                />
              </div>

              <div className="space-y-1.5">
                <label htmlFor="password" className="block text-sm font-medium text-slate-300">
                  Password
                </label>
                <input
                  id="password"
                  className="w-full rounded-lg border border-slate-700/60 bg-slate-900 px-3.5 py-2.5 text-sm text-slate-100 outline-none transition-colors focus:border-sky-500/60"
                  placeholder="••••••••"
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  autoComplete="current-password"
                />
              </div>

              <button
                disabled={isSubmitting}
                className="w-full rounded-lg bg-sky-500 px-4 py-2.5 text-sm font-semibold text-slate-950 transition-colors hover:bg-sky-400 disabled:cursor-not-allowed disabled:opacity-60"
              >
                {isSubmitting ? 'Signing in...' : 'Enter control tower'}
              </button>
            </form>

            <div className="border-t border-slate-800/60 pt-4 text-center">
              <p className="text-xs text-slate-500">New workspace? Create the company account on the product site first.</p>
              <a
                href={signupUrl}
                className="mt-1.5 inline-block text-sm font-medium text-sky-400 underline-offset-4 hover:underline"
                target="_blank"
                rel="noreferrer"
              >
                Create company account →
              </a>
            </div>

            <div className="text-center">
              <button
                type="button"
                disabled={isBootstrapping}
                onClick={onBootstrapInitialAdmin}
                className="text-xs font-medium text-slate-500 underline-offset-4 transition-colors hover:text-slate-300 hover:underline disabled:cursor-not-allowed disabled:opacity-60"
              >
                {isBootstrapping ? 'Creating admin...' : 'Create initial admin (first-time setup)'}
              </button>
            </div>

            {error ? (
              <div className="rounded-lg border border-rose-500/25 bg-rose-950/30 px-3.5 py-3 text-sm text-rose-300">
                {error}
              </div>
            ) : null}
          </div>
        </section>
      </div>
    </div>
  );
}

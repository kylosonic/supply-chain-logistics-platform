import { useState } from 'react';
import { useNavigate } from 'react-router-dom';

import { apiErrorMessage } from '../services/authErrors';
import { setStoredToken } from '../services/api';
import { acceptInvitation } from '../services/teamApi';

const FIELD =
  'mt-1 min-h-12 w-full rounded-lg border border-slate-700 bg-slate-950/70 px-3 text-sm text-slate-100 outline-none transition focus:border-sky-400';

export function AcceptInvitePage() {
  const navigate = useNavigate();
  const fragment = typeof window === 'undefined' ? '' : window.location.hash.replace(/^#/, '');
  const token = new URLSearchParams(fragment).get('token') || '';
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [fullName, setFullName] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  async function onSubmit(event: React.FormEvent) {
    event.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      const result = await acceptInvitation({
        token,
        username,
        password,
        full_name: fullName || undefined,
      });
      setStoredToken(result.access_token);
      navigate('/', { replace: true });
      window.location.reload();
    } catch (err) {
      setError(apiErrorMessage(err, 'Could not accept the invitation.'));
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <main className="flex min-h-screen items-center justify-center bg-[var(--fp-black)] px-4 py-10 text-slate-100">
      <section className="fp-shell-surface w-full max-w-lg p-6 sm:p-8">
        <p className="text-xs font-medium uppercase tracking-[0.18em] text-sky-300">FreightPilot workspace</p>
        <h1 className="mt-3 font-['Space_Grotesk'] text-3xl font-semibold">Accept your invitation</h1>
        <p className="mt-3 text-sm leading-7 text-slate-400">
          Create the account that will join the workspace. If the email already has an account,
          enter that account's existing password.
        </p>

        {!token ? (
          <p className="mt-5 rounded-lg border border-rose-500/25 bg-rose-950/25 p-3 text-sm text-rose-200">
            This invitation link is missing a token.
          </p>
        ) : (
          <form onSubmit={onSubmit} className="mt-6 space-y-4">
            <label className="block text-xs font-medium text-slate-400">
              Username
              <input
                className={FIELD}
                required
                minLength={3}
                value={username}
                onChange={(event) => setUsername(event.target.value)}
                autoComplete="username"
              />
            </label>
            <label className="block text-xs font-medium text-slate-400">
              Full name <span className="font-normal text-slate-600">(optional)</span>
              <input
                className={FIELD}
                value={fullName}
                onChange={(event) => setFullName(event.target.value)}
                autoComplete="name"
              />
            </label>
            <label className="block text-xs font-medium text-slate-400">
              Password
              <input
                className={FIELD}
                type="password"
                required
                minLength={8}
                value={password}
                onChange={(event) => setPassword(event.target.value)}
                autoComplete="new-password"
              />
            </label>
            {error ? <p className="text-sm text-rose-300">{error}</p> : null}
            <button
              className="w-full rounded-lg bg-sky-500 px-4 py-3 text-sm font-semibold text-slate-950 hover:bg-sky-400 disabled:opacity-60"
              disabled={submitting}
            >
              {submitting ? 'Joining workspace…' : 'Join workspace'}
            </button>
          </form>
        )}
      </section>
    </main>
  );
}

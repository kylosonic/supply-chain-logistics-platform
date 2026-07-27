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
    <div className="mx-auto max-w-md rounded-xl bg-white p-6 shadow-sm ring-1 ring-slate-200">
      <h1 className="mb-4 text-xl font-semibold text-slate-900">Login</h1>
      <form className="space-y-3" onSubmit={onSubmit}>
        <input
          className="w-full rounded border px-3 py-2"
          placeholder="Company email or username"
          value={identifier}
          onChange={(e) => setIdentifier(e.target.value)}
        />
        <input
          className="w-full rounded border px-3 py-2"
          placeholder="Password"
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
        />
        <button disabled={isSubmitting} className="w-full rounded bg-slate-900 px-3 py-2 text-white">
          {isSubmitting ? 'Signing in...' : 'Sign in'}
        </button>
        <button
          type="button"
          disabled={isBootstrapping}
          onClick={onBootstrapInitialAdmin}
          className="w-full rounded border border-slate-400 px-3 py-2 text-slate-700"
        >
          {isBootstrapping ? 'Creating admin...' : 'Create initial admin'}
        </button>
      </form>
      {error ? <p className="mt-3 text-sm text-red-600">{error}</p> : null}
      <div className="mt-4 space-y-2 text-xs text-slate-500">
        <p>Use your company account credentials. If your company is new, create an account from the product site.</p>
        <a href={signupUrl} className="font-semibold text-slate-700 underline" target="_blank" rel="noreferrer">
          Create company account
        </a>
      </div>
    </div>
  );
}

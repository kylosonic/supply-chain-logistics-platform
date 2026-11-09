import { useEffect, useState } from 'react';

import { getCustomerTracking } from '../services/dispatchApi';
import type { CustomerTrackingView } from '../types/api';

function formatTime(value: string | null): string {
  if (!value) return 'Not set';
  return new Date(value).toLocaleString([], {
    dateStyle: 'medium',
    timeStyle: 'short',
  });
}

const statusLabel: Record<string, string> = {
  planned: 'Preparing',
  assigned: 'Assigned',
  in_transit: 'On the way',
  delivered: 'Delivered',
  failed: 'Delivery issue',
  cancelled: 'Cancelled',
};

export function TrackingPage() {
  const fragment =
    typeof window === 'undefined' ? '' : window.location.hash.replace(/^#/, '');
  const token = new URLSearchParams(fragment).get('token') || '';
  const [tracking, setTracking] = useState<CustomerTrackingView | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!token) {
      setError('This tracking link is incomplete.');
      setLoading(false);
      return;
    }
    let active = true;
    async function load() {
      try {
        const next = await getCustomerTracking(token);
        if (!active) return;
        setTracking(next);
        setError(null);
      } catch (err) {
        if (!active) return;
        setError(err instanceof Error ? err.message : 'Could not load this delivery.');
      } finally {
        if (active) setLoading(false);
      }
    }
    void load();
    const timer = window.setInterval(() => void load(), 30_000);
    return () => {
      active = false;
      window.clearInterval(timer);
    };
  }, [token]);

  return (
    <main className="min-h-screen bg-[var(--fp-black)] px-4 py-8 text-slate-100">
      <div className="mx-auto max-w-xl space-y-4">
        <header>
          <p className="text-xs font-semibold uppercase tracking-[0.2em] text-sky-300">
            FreightPilot Tracking
          </p>
          <h1 className="mt-2 font-['Space_Grotesk'] text-3xl font-semibold">
            {tracking ? `Order ${tracking.order_no}` : 'Delivery status'}
          </h1>
        </header>

        {loading ? (
          <div className="space-y-3 border border-slate-800 p-5" role="status">
            <div className="skeleton h-6 w-1/2" />
            <div className="skeleton h-20" />
          </div>
        ) : null}

        {error ? (
          <p className="rounded-lg border border-rose-500/25 bg-rose-950/30 p-4 text-sm text-rose-200">
            {error}
          </p>
        ) : null}

        {tracking ? (
          <section className="space-y-5 rounded-xl border border-slate-800 bg-slate-950/60 p-5">
            <div className="flex flex-wrap items-start justify-between gap-3">
              <div>
                <p className="text-sm text-slate-400">{tracking.customer_name}</p>
                <p className="mt-1 font-['Space_Grotesk'] text-2xl font-semibold text-sky-100">
                  {statusLabel[tracking.status] ?? tracking.status}
                </p>
              </div>
              <span className="rounded-full border border-sky-500/30 px-3 py-1 text-xs font-semibold text-sky-200">
                {tracking.proof_available ? 'Proof recorded' : 'Proof pending'}
              </span>
            </div>

            <div className="grid gap-4 text-sm sm:grid-cols-2">
              <div>
                <p className="text-xs uppercase tracking-wide text-slate-500">Estimated arrival</p>
                <p className="mt-1 text-slate-200">{formatTime(tracking.planned_arrival)}</p>
              </div>
              <div>
                <p className="text-xs uppercase tracking-wide text-slate-500">Delivery window</p>
                <p className="mt-1 text-slate-200">
                  {formatTime(tracking.window_start)} to {formatTime(tracking.window_end)}
                </p>
              </div>
              <div>
                <p className="text-xs uppercase tracking-wide text-slate-500">Route</p>
                <p className="mt-1 text-slate-200">{tracking.route_name ?? 'Not assigned'}</p>
              </div>
              <div>
                <p className="text-xs uppercase tracking-wide text-slate-500">Driver</p>
                <p className="mt-1 text-slate-200">{tracking.driver_name ?? 'Not assigned'}</p>
              </div>
            </div>

            <p className="border-t border-slate-800 pt-4 text-xs text-slate-500">
              Last updated {formatTime(tracking.updated_at)}
            </p>
          </section>
        ) : null}
      </div>
    </main>
  );
}

'use client';

import { useEffect, useState } from 'react';

type ProbeState = {
  state: 'checking' | 'ok' | 'degraded' | 'unreachable';
  db: string | null;
  checkedAt: string | null;
};

const apiBase = (process.env.NEXT_PUBLIC_PLATFORM_API_URL || '').replace(/\/$/, '');
const healthUrl = apiBase ? `${apiBase.replace(/\/api\/v1$/, '')}/health` : '';

export function StatusProbe() {
  const [probe, setProbe] = useState<ProbeState>({
    state: 'checking',
    db: null,
    checkedAt: null,
  });

  useEffect(() => {
    let cancelled = false;

    async function check() {
      if (!healthUrl) {
        setProbe({ state: 'unreachable', db: null, checkedAt: null });
        return;
      }
      try {
        const response = await fetch(healthUrl, { cache: 'no-store' });
        if (!response.ok) throw new Error(`Health probe returned ${response.status}`);
        const body = (await response.json()) as { status?: string; db?: string };
        if (cancelled) return;
        setProbe({
          state: body.status === 'ok' && body.db === 'ok' ? 'ok' : 'degraded',
          db: body.db ?? null,
          checkedAt: new Date().toISOString(),
        });
      } catch {
        if (cancelled) return;
        setProbe({ state: 'unreachable', db: null, checkedAt: new Date().toISOString() });
      }
    }

    void check();
    const timer = window.setInterval(check, 30_000);
    return () => {
      cancelled = true;
      window.clearInterval(timer);
    };
  }, []);

  const label = {
    checking: 'Checking…',
    ok: 'All reported checks healthy',
    degraded: 'Service reachable, database degraded',
    unreachable: 'Status probe unavailable',
  }[probe.state];

  return (
    <div className="rounded-2xl border border-white/10 bg-white/[0.04] p-5 sm:p-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <p className="kicker">Platform API</p>
          <p className="mt-2 font-display text-2xl text-white">{label}</p>
        </div>
        <span
          className={`inline-flex rounded-full border px-3 py-1 text-xs font-semibold ${
            probe.state === 'ok'
              ? 'border-emerald-400/30 bg-emerald-950/40 text-emerald-200'
              : probe.state === 'checking'
                ? 'border-white/15 bg-white/5 text-white/60'
                : 'border-amber-400/30 bg-amber-950/30 text-amber-200'
          }`}
        >
          {probe.state.toUpperCase()}
        </span>
      </div>
      <p className="mt-4 text-sm leading-7 text-white/55">
        Database: {probe.db ?? 'not reported'} · Last checked:{' '}
        {probe.checkedAt ? new Date(probe.checkedAt).toLocaleString() : 'pending'}
      </p>
      <p className="mt-2 text-xs leading-6 text-white/40">
        This probe is intentionally limited to the public health endpoint. It is not a substitute
        for an incident notification or a contractual support channel.
      </p>
    </div>
  );
}

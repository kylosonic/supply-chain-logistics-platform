import { Link } from 'react-router-dom';

import { useActivationState, useDismissPitch } from '../hooks/queries';

// Free-cap + upgrade-pitch banners — ONE shared rendering,
// mounted in the Layout slot on EVERY console page. The activation/demo
// banner (ActivationBanner) is page-level on /dashboard + /upload only
//. Stack priority is server-derived (decision #6): p100 > p80 > p60.

const P100_MESSAGE =
  'Free tier cap reached. Writes resume next month, or upgrade now to continue immediately.';

export function CapPitchBanner() {
  const activationQ = useActivationState();
  const dismiss = useDismissPitch();

  const state = activationQ.data;
  if (!state) return null;

  const locked = state.free_cap?.locked ?? false;
  const level = locked ? 'p100' : state.pitch?.banner ?? null;
  if (!level) return null;

  if (level === 'p100') {
    return (
      <div
        role="banner"
        data-testid="cap-pitch-banner"
        className="mb-5 flex flex-wrap items-center justify-between gap-3 rounded-xl border border-rose-500/20 bg-rose-950/25 px-5 py-4"
      >
        <p className="text-sm font-semibold leading-6 text-rose-100">
          {state.free_cap?.message ?? P100_MESSAGE}
        </p>
        <Link
          to="/account"
          className="glow-ring inline-flex min-h-10 items-center justify-center rounded-lg bg-rose-600 px-4 text-sm font-semibold text-white transition-colors hover:bg-rose-500"
        >
          Upgrade now
        </Link>
      </div>
    );
  }

  if (level === 'p80') {
    return (
      <div
        role="banner"
        data-testid="cap-pitch-banner"
        className="mb-5 flex flex-wrap items-center justify-between gap-3 rounded-xl border border-amber-500/20 bg-amber-950/25 px-5 py-4"
      >
        <p className="text-sm font-semibold leading-6 text-amber-100">
          You&apos;ve used 80% of your Free tier tasks. Consider upgrading before writes lock.
        </p>
        <Link
          to="/account"
          className="glow-ring inline-flex min-h-10 items-center justify-center rounded-full border border-amber-500/40 px-4 text-sm font-semibold text-amber-100 transition hover:border-amber-400/60 hover:bg-amber-950/40"
        >
          See pricing
        </Link>
      </div>
    );
  }

  return (
    <div
      role="banner"
      data-testid="cap-pitch-banner"
      className="mb-5 flex flex-wrap items-center justify-between gap-3 rounded-xl border border-slate-800/60 bg-slate-900/35 px-5 py-4"
    >
      <p className="text-sm font-semibold leading-6 text-slate-200">
        You&apos;ve used 60% of your Free tier tasks this month.
      </p>
      <button
        type="button"
        onClick={() => dismiss.mutate('p60')}
        className="rounded-full border border-slate-600 px-3 py-1.5 text-xs font-semibold text-slate-300 transition hover:border-slate-400 hover:bg-slate-800"
      >
        Dismiss
      </button>
    </div>
  );
}

// Activation / demo banner (decision #8 + NB-34 copy matrix).
// mode="compact": /dashboard. mode="checklist": /upload.
// Renders NOTHING once milestone 6 completes.

const CATEGORY_ORDER = ['Warehouses', 'Items', 'Fleet Assets', 'Inventory', 'Orders'];

export function ActivationBanner({ mode }: { mode: 'compact' | 'checklist' }) {
  const activationQ = useActivationState();
  const state = activationQ.data;
  if (!state || state.m6_completed || !state.banner.visible) return null;

  const n = state.n_of_5;
  const pct = state.pct_complete;

  if (mode === 'compact') {
    return (
      <div
        role="banner"
        data-testid="activation-banner"
        className="flex flex-wrap items-center justify-between gap-3 rounded-2xl border border-slate-800/60 bg-slate-900/35 px-5 py-4"
      >
        <div>
          {n < 5 ? (
            <p className="text-sm font-semibold leading-6 text-sky-100">
              Welcome back. You&apos;re {pct}% through onboarding — {5 - n} step
              {5 - n === 1 ? '' : 's'} remaining ({CATEGORY_ORDER.slice(n).join(', ')}). Continue
              setup.
            </p>
          ) : (
            <p className="text-sm font-semibold leading-6 text-sky-100">
              Welcome back. You&apos;re 80% through onboarding — run your first route optimization
              to complete setup.
            </p>
          )}
          <div className="mt-2 h-1.5 w-full max-w-[420px] overflow-hidden rounded-full bg-slate-800">
            <div
              className="h-full rounded-lg bg-sky-500"
              style={{ width: `${pct}%` }}
            />
          </div>
        </div>
        <Link
          to={state.banner.cta ?? '/upload'}
          className="glow-ring inline-flex min-h-10 items-center justify-center rounded-lg bg-sky-500 px-4 text-sm font-semibold text-slate-950 transition-colors hover:bg-sky-400"
        >
          {n < 5 ? 'Continue setup' : 'Run your first route'}
        </Link>
      </div>
    );
  }

  return (
    <div
      role="banner"
      data-testid="activation-checklist"
      className="rounded-2xl border border-slate-800/60 bg-slate-900/35 p-5"
    >
      {n < 5 ? (
        <p className="text-sm font-semibold leading-6 text-sky-100">
          You&apos;re viewing a demo workspace with sample data. Upload your real CSVs to start
          replacing the demo with your operation — {n} of 5 categories is yours.
        </p>
      ) : (
        <div className="flex flex-wrap items-center justify-between gap-3">
          <p className="text-sm font-semibold leading-6 text-sky-100">
            Welcome back. You&apos;re 80% through onboarding — run your first route optimization to
            complete setup.
          </p>
          <Link
            to="/routes"
            className="glow-ring inline-flex min-h-10 items-center justify-center rounded-lg bg-sky-500 px-4 text-sm font-semibold text-slate-950 transition-colors hover:bg-sky-400"
          >
            Run your first route
          </Link>
        </div>
      )}

      <div className="mt-4 grid gap-2 md:grid-cols-5">
        {state.milestones.map((milestone, index) => {
          const chipTone =
            milestone.status === 'real'
              ? 'border-emerald-500/40 bg-emerald-950/30 text-emerald-200'
              : milestone.status === 'sample'
                ? 'border-amber-500/30 bg-amber-950/20 text-amber-200'
                : 'border-slate-700 bg-slate-900/60 text-slate-400';
          return (
            <div
              key={milestone.category}
              data-testid={`milestone-chip-${milestone.category}`}
              className={`rounded-xl border px-3 py-3 ${chipTone}`}
            >
              <div className="flex items-center justify-between gap-2">
                <p className="text-xs font-semibold uppercase tracking-wide">
                  Step {index + 1}
                </p>
                <span className="rounded-full border border-slate-700/70 px-2 py-0.5 text-[10px] font-bold uppercase tracking-wide">
                  {milestone.status}
                </span>
              </div>
              <p className="mt-2 text-sm font-semibold">{milestone.label}</p>
              {index === n && !state.m6_completed ? (
                <p className="mt-1 text-[11px] font-semibold text-sky-400">next step →</p>
              ) : null}
            </div>
          );
        })}
      </div>

      <div className="mt-4 h-1.5 overflow-hidden rounded-full bg-slate-800">
        <div
          className="h-full rounded-lg bg-sky-500"
          style={{ width: `${pct}%` }}
        />
      </div>
      <p className="mt-2 text-xs text-slate-400">
        {n < 5 ? `${5 - n} step${5 - n === 1 ? '' : 's'} remaining.` : 'Run your first route optimization to complete setup.'}
      </p>
    </div>
  );
}


import type { RouteDecisionExplanation } from '../types/api';

const FACTOR_LABELS: Record<string, string> = {
  distance: 'Distance',
  time: 'Travel time',
  cost: 'Monetary cost',
  none: 'No weighted factor',
};

const FACTOR_COLORS: Record<string, string> = {
  distance: 'bg-sky-400',
  time: 'bg-emerald-400',
  cost: 'bg-amber-400',
  none: 'bg-slate-600',
};

export function RouteDecisionBrief({
  explanation,
}: {
  explanation?: RouteDecisionExplanation | null;
}) {
  if (!explanation) {
    return (
      <div className="rounded-[var(--fp-radius-panel)] border border-dashed border-slate-700/60 bg-slate-900/30 px-4 py-3">
        <p className="text-sm font-semibold text-slate-300">Why this route</p>
        <p className="mt-1 text-sm text-slate-500">
          No explanation was recorded for this run. New optimizations include one automatically.
        </p>
      </div>
    );
  }

  return (
    <section className="rounded-[var(--fp-radius-panel)] border border-sky-500/20 bg-sky-950/10 p-4">
      <div className="flex flex-wrap items-start justify-between gap-2">
        <div>
          <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-sky-300">Why this route</p>
          <h3 className="mt-1 font-['Space_Grotesk'] text-lg font-semibold text-slate-50">
            {FACTOR_LABELS[explanation.dominant_factor] ?? explanation.dominant_factor} led this plan
          </h3>
        </div>
        <span className="rounded-full border border-slate-700/70 px-2.5 py-1 text-[11px] font-medium text-slate-400">
          derived from run inputs
        </span>
      </div>

      <p className="mt-3 text-sm leading-6 text-slate-300">{explanation.summary}</p>

      <div className="mt-4 grid gap-2 sm:grid-cols-3">
        {(['distance', 'time', 'cost'] as const).map((factor) => (
          <div key={factor} className="rounded-xl border border-slate-800/70 bg-slate-950/25 px-3 py-2.5">
            <div className="flex items-center justify-between gap-2 text-xs">
              <span className="text-slate-400">{FACTOR_LABELS[factor]}</span>
              <span className="font-mono tabular-nums text-slate-200">
                {explanation.factor_share_pct[factor].toFixed(1)}%
              </span>
            </div>
            <div className="mt-2 h-1.5 overflow-hidden rounded-full bg-slate-800">
              <div
                className={`h-full rounded-full ${FACTOR_COLORS[factor]}`}
                style={{ width: `${Math.min(100, Math.max(0, explanation.factor_share_pct[factor]))}%` }}
              />
            </div>
          </div>
        ))}
      </div>

      {explanation.constraints.length > 0 ? (
        <div className="mt-3 rounded-xl border border-amber-500/20 bg-amber-950/10 px-3 py-2.5">
          <p className="text-xs font-semibold uppercase tracking-wide text-amber-200">Constraints in effect</p>
          <ul className="mt-1 space-y-1 text-sm text-slate-300">
            {explanation.constraints.map((constraint) => (
              <li key={constraint}>{constraint}</li>
            ))}
          </ul>
        </div>
      ) : null}

      {explanation.runner_up ? (
        <div className="mt-3 rounded-xl border border-slate-800/70 bg-slate-900/40 px-3 py-2.5">
          <p className="text-xs font-semibold uppercase tracking-wide text-slate-400">Runner-up scenario</p>
          <p className="mt-1 text-sm text-slate-300">{explanation.runner_up.summary}</p>
        </div>
      ) : null}

      {explanation.decision_points.length > 0 ? (
        <details className="mt-3 rounded-xl border border-slate-800/70 bg-slate-900/30 px-3 py-2.5">
          <summary className="cursor-pointer text-sm font-semibold text-slate-300">
            Decision-by-decision evidence ({explanation.decision_points.length})
          </summary>
          <ol className="mt-3 space-y-2">
            {explanation.decision_points.map((point) => (
              <li key={point.sequence} className="border-t border-slate-800/60 pt-2 text-sm text-slate-400 first:border-t-0 first:pt-0">
                <span className="font-semibold text-slate-200">#{point.sequence} {point.chosen_warehouse_code}</span>
                {' — '}
                {point.reason}
              </li>
            ))}
          </ol>
        </details>
      ) : null}

      <p className="mt-3 text-[11px] leading-5 text-slate-500">{explanation.limitations.join(' ')}</p>
    </section>
  );
}

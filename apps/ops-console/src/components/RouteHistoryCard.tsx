import { useState } from 'react';

import { loadRouteHistoryDetail } from '../services/routeHistoryDetail';
import type { RouteOptimizationRunDetail, RouteOptimizationRunSummary } from '../types/api';
import { RouteDecisionBrief } from './RouteDecisionBrief';
import { StatusBadge } from './ui/StatusBadge';

export function RouteHistoryCard({ run }: { run: RouteOptimizationRunSummary }) {
  const [expanded, setExpanded] = useState(false);
  const [detail, setDetail] = useState<RouteOptimizationRunDetail | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function toggleExplanation() {
    if (expanded) {
      setExpanded(false);
      return;
    }

    setExpanded(true);
    if (detail) return;

    setIsLoading(true);
    setError(null);
    const loaded = await loadRouteHistoryDetail(run.id);
    setDetail(loaded.detail);
    setError(loaded.error);
    setIsLoading(false);
  }

  return (
    <article className="fp-row">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <div className="flex flex-wrap items-center gap-2">
            <StatusBadge
              label={run.persist_requested ? 'persisted run' : 'draft run'}
              tone={run.persist_requested ? 'success' : 'info'}
            />
            {run.unassigned_count > 0 ? (
              <StatusBadge label={`${run.unassigned_count} unassigned`} tone="warning" />
            ) : null}
          </div>
          <h3 className="mt-2 font-['Space_Grotesk'] text-lg font-semibold text-slate-50">{run.route_name}</h3>
          <p className="mt-1 text-sm text-slate-400">
            {run.schedule_date} from {run.start_warehouse_code}
          </p>
        </div>
        <span className="text-xs text-slate-500">{new Date(run.created_at).toLocaleString()}</span>
      </div>

      <div className="mt-3 grid gap-2 text-sm text-slate-400 sm:grid-cols-4">
        <span>
          <span className="font-mono font-semibold tabular-nums text-slate-200">{run.total_distance_km}</span> km
        </span>
        <span>
          <span className="font-mono font-semibold tabular-nums text-slate-200">${run.total_cost}</span>
        </span>
        <span>
          <span className="font-mono font-semibold tabular-nums text-slate-200">{run.estimated_duration_min}</span> min
        </span>
        <span>
          <span className="font-mono font-semibold tabular-nums text-slate-200">{run.deliveries_count}</span> deliveries
        </span>
      </div>

      <button
        type="button"
        onClick={toggleExplanation}
        aria-expanded={expanded}
        className="glow-ring mt-3 inline-flex min-h-9 items-center rounded-full border border-sky-500/30 px-3 text-xs font-semibold text-sky-200 transition hover:border-sky-400/50 hover:bg-sky-950/20"
      >
        {expanded ? 'Hide explanation' : 'Why this route'}
      </button>

      {expanded ? (
        <RouteHistoryExplanationState
          isLoading={isLoading}
          error={error}
          detail={detail}
        />
      ) : null}
    </article>
  );
}

export function RouteHistoryExplanationState({
  isLoading,
  error,
  detail,
}: {
  isLoading: boolean;
  error: string | null;
  detail: RouteOptimizationRunDetail | null;
}) {
  return (
    <div className="mt-3">
      {isLoading ? <div className="skeleton h-32" /> : null}
      {error ? (
        <p className="rounded-xl border border-rose-500/20 bg-rose-950/15 px-3 py-2 text-sm text-rose-200">
          {error}
        </p>
      ) : null}
      {!isLoading && !error ? (
        <RouteDecisionBrief explanation={detail?.decision_explanation} />
      ) : null}
    </div>
  );
}

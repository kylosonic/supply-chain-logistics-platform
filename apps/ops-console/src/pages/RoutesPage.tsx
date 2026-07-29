import { useEffect, useState } from 'react';

import { RouteMap } from '../components/RouteMap';
import { RouteOptimizerForm } from '../components/RouteOptimizerForm';
import { RouteSchedulesTable } from '../components/RouteSchedulesTable';
import { PageHeader } from '../components/ui/PageHeader';
import { Panel } from '../components/ui/Panel';
import { StatusBadge } from '../components/ui/StatusBadge';
import { useAuth } from '../context/AuthContext';
import { useLiveUpdates } from '../hooks/useLiveUpdates';
import { getRouteOptimizationHistory, getRouteSchedules } from '../services/logisticsApi';
import type { RouteOptimizationRunSummary, RouteOptimizeResponse, RouteScheduleSummary, RouteStop } from '../types/api';

export function RoutesPage() {
  const { token } = useAuth();
  const [schedules, setSchedules] = useState<RouteScheduleSummary[]>([]);
  const [history, setHistory] = useState<RouteOptimizationRunSummary[]>([]);
  const [latestRouteStops, setLatestRouteStops] = useState<RouteStop[]>([]);
  const [error, setError] = useState<string | null>(null);

  async function loadSchedules() {
    try {
      setError(null);
      const [scheduleData, historyData] = await Promise.all([getRouteSchedules(), getRouteOptimizationHistory()]);
      setSchedules(scheduleData);
      setHistory(historyData);
    } catch (err: any) {
      setError(err?.response?.data?.detail || err.message || 'Failed to load route schedules');
    }
  }

  useEffect(() => {
    loadSchedules();
  }, []);

  useLiveUpdates({
    token,
    onMessage: (payload) => {
      setSchedules(payload.route_summaries);
    },
  });

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Route studio"
        title="Build, compare, and operationalize route scenarios"
        description="Optimize a dispatch plan, review the resulting path, and keep the saved schedule book visible for the wider team."
        actions={
          <button
            onClick={loadSchedules}
            className="inline-flex min-h-10 items-center justify-center rounded-full border border-slate-700 px-4 text-sm font-semibold text-slate-200 transition hover:border-slate-500 hover:bg-slate-900"
          >
            Refresh schedules
          </button>
        }
      />

      {error ? (
        <Panel className="border-rose-500/25 bg-rose-950/12">
          <p className="text-sm text-rose-200">{error}</p>
        </Panel>
      ) : null}

      <div className="grid grid-cols-1 gap-5 xl:grid-cols-[1.05fr_0.95fr]">
        <RouteOptimizerForm
          onOptimized={(route: RouteOptimizeResponse) => {
            setLatestRouteStops(route.stops);
            loadSchedules();
          }}
        />
        <RouteMap stops={latestRouteStops} />
      </div>

      <Panel
        eyebrow="Schedule library"
        title="Saved route schedules"
        description="Operational route outputs persist here so the team can reference the latest optimized plans."
      >
        <RouteSchedulesTable schedules={schedules} />
      </Panel>

      <Panel
        eyebrow="Scenario history"
        title="Recent route optimization runs"
        description="Every optimization run now keeps a scenario record so the team can review what was modeled, what persisted, and where manual intervention was still required."
      >
        <div className="space-y-3">
          {history.slice(0, 6).map((run) => (
            <article key={run.id} className="rounded-[22px] border border-slate-800 bg-slate-900/70 p-4">
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div>
                  <div className="flex flex-wrap items-center gap-2">
                    <StatusBadge label={run.persist_requested ? 'persisted run' : 'draft run'} tone={run.persist_requested ? 'success' : 'info'} />
                    {run.unassigned_count > 0 ? <StatusBadge label={`${run.unassigned_count} unassigned`} tone="warning" /> : null}
                  </div>
                  <h3 className="mt-2 font-['Space_Grotesk'] text-lg font-semibold text-slate-50">{run.route_name}</h3>
                  <p className="mt-1 text-sm text-slate-400">{run.schedule_date} from {run.start_warehouse_code}</p>
                </div>
                <span className="text-xs text-slate-500">{new Date(run.created_at).toLocaleString()}</span>
              </div>
              <div className="mt-3 grid gap-2 text-sm text-slate-400 sm:grid-cols-4">
                <span>{run.total_distance_km} km</span>
                <span>${run.total_cost}</span>
                <span>{run.estimated_duration_min} min</span>
                <span>{run.deliveries_count} deliveries</span>
              </div>
            </article>
          ))}

          {history.length === 0 ? <p className="text-sm text-slate-500">No optimization history yet.</p> : null}
        </div>
      </Panel>
    </div>
  );
}

import { useEffect, useState } from 'react';

import { PostAhaToast } from '../components/PostAhaToast';
import { RouteMap } from '../components/RouteMap';
import { RouteOptimizerForm } from '../components/RouteOptimizerForm';
import { RouteSchedulesTable } from '../components/RouteSchedulesTable';
import { PageHeader } from '../components/ui/PageHeader';
import { Panel } from '../components/ui/Panel';
import { StatusBadge } from '../components/ui/StatusBadge';
import { useAuth } from '../context/AuthContext';
import { useActivationState } from '../hooks/queries';
import { useLiveUpdates } from '../hooks/useLiveUpdates';
import { getRouteOptimizationHistory, getRouteSchedules, getWeatherRiskZones } from '../services/logisticsApi';
import type { RouteOptimizationRunSummary, RouteOptimizeResponse, RouteScheduleSummary, RouteStop, WeatherRiskZone } from '../types/api';

export function RoutesPage() {
  const { getToken, user } = useAuth();
  const activationQ = useActivationState();
  const [schedules, setSchedules] = useState<RouteScheduleSummary[]>([]);
  const [history, setHistory] = useState<RouteOptimizationRunSummary[]>([]);
  const [riskZones, setRiskZones] = useState<WeatherRiskZone[]>([]);
  const [latestRouteStops, setLatestRouteStops] = useState<RouteStop[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [postAhaVisible, setPostAhaVisible] = useState(false);

  // NB-29.1: the weather risk zones map unlocks at milestone 5; the page
  // itself remains routable (NB-28.5) — optimize 423s only on locks.
  const milestone = activationQ.data?.m6_completed ? 6 : (activationQ.data?.n_of_5 ?? 0);
  const weatherMapUnlocked = milestone >= 5;

  async function loadSchedules() {
    try {
      setError(null);
      const [scheduleData, historyData, riskData] = await Promise.all([
        getRouteSchedules(),
        getRouteOptimizationHistory(),
        getWeatherRiskZones().catch(() => [])
      ]);
      setSchedules(scheduleData);
      setHistory(historyData);
      setRiskZones(riskData);
    } catch (err: any) {
      setError(err?.response?.data?.detail || err.message || 'Failed to load route schedules');
    }
  }

  useEffect(() => {
    loadSchedules();
  }, []);

  useLiveUpdates({ getToken, enabled: Boolean(user), onMessage: (payload) => {
    setSchedules(payload.route_summaries);
  }});

  async function handleRefresh() {
    setIsRefreshing(true);
    await loadSchedules();
    setIsRefreshing(false);
  }

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Route studio"
        title="Build, compare, and operationalize route scenarios"
        description="Optimize a dispatch plan, review the resulting path, and keep the saved schedule book visible for the wider team."
        actions={
          <button
            onClick={handleRefresh}
            className="glow-ring inline-flex min-h-10 items-center justify-center gap-2 rounded-full border border-slate-700 px-4 text-sm font-semibold text-slate-200 transition hover:border-slate-500 hover:bg-slate-900"
          >
            {isRefreshing ? (
              <svg className="animate-spin-slow h-4 w-4" viewBox="0 0 24 24" fill="none"><circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeDasharray="50 20" /></svg>
            ) : null}
            {isRefreshing ? 'Refreshing...' : 'Refresh schedules'}
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
            // NB-33: fire the one-time toast exactly when the server says
            // this was the org's FIRST optimization (server truth).
            if (route.post_aha_toast) {
              setPostAhaVisible(true);
            }
          }}
        />
        {weatherMapUnlocked ? (
          <RouteMap stops={latestRouteStops} riskZones={riskZones} />
        ) : (
          <Panel eyebrow="Weather risk" title="Weather risk zones map">
            <div className="grid h-full min-h-[240px] place-items-center rounded-[24px] border border-dashed border-slate-700/80 bg-slate-900/40 p-6 text-center">
              <div>
                <p className="font-['Space_Grotesk'] text-lg font-semibold text-slate-300">
                  Unlocks after Milestone 5
                </p>
                <a href="/upload" className="mt-2 inline-block text-sm font-semibold text-sky-300 underline-offset-4 hover:underline">
                  Continue onboarding →
                </a>
              </div>
            </div>
          </Panel>
        )}
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
          {history.slice(0, 6).map((run, index) => (
            <article key={run.id} className="animate-fade-in hover-lift rounded-[22px] border border-slate-800 bg-slate-900/70 p-4" style={{ animationDelay: `${index * 0.04}s` }}>
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
                <span><span className="font-semibold text-slate-200">{run.total_distance_km}</span> km</span>
                <span><span className="font-semibold text-slate-200">${run.total_cost}</span></span>
                <span><span className="font-semibold text-slate-200">{run.estimated_duration_min}</span> min</span>
                <span><span className="font-semibold text-slate-200">{run.deliveries_count}</span> deliveries</span>
              </div>
            </article>
          ))}

          {history.length === 0 ? (
            <div className="animate-fade-in rounded-[22px] border border-slate-800 bg-slate-900/40 p-6 text-center">
              <p className="font-['Space_Grotesk'] text-lg font-semibold text-slate-300">No optimization history</p>
              <p className="mt-1 text-sm text-slate-500">Run a route optimization above to start building scenario history.</p>
            </div>
          ) : null}
        </div>
      </Panel>

      <PostAhaToast visible={postAhaVisible} onDismiss={() => setPostAhaVisible(false)} />
    </div>
  );
}

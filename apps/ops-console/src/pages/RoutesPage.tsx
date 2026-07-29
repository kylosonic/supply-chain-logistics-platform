import { useEffect, useState } from 'react';

import { RouteMap } from '../components/RouteMap';
import { RouteOptimizerForm } from '../components/RouteOptimizerForm';
import { RouteSchedulesTable } from '../components/RouteSchedulesTable';
import { PageHeader } from '../components/ui/PageHeader';
import { Panel } from '../components/ui/Panel';
import { useAuth } from '../context/AuthContext';
import { useLiveUpdates } from '../hooks/useLiveUpdates';
import { getRouteSchedules } from '../services/logisticsApi';
import type { RouteOptimizeResponse, RouteScheduleSummary, RouteStop } from '../types/api';

export function RoutesPage() {
  const { token } = useAuth();
  const [schedules, setSchedules] = useState<RouteScheduleSummary[]>([]);
  const [latestRouteStops, setLatestRouteStops] = useState<RouteStop[]>([]);
  const [error, setError] = useState<string | null>(null);

  async function loadSchedules() {
    try {
      setError(null);
      const data = await getRouteSchedules();
      setSchedules(data);
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
    </div>
  );
}

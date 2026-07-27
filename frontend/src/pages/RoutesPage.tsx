import { useEffect, useState } from 'react';

import { RouteMap } from '../components/RouteMap';
import { RouteOptimizerForm } from '../components/RouteOptimizerForm';
import { RouteSchedulesTable } from '../components/RouteSchedulesTable';
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
      <RouteOptimizerForm
        onOptimized={(route: RouteOptimizeResponse) => {
          setLatestRouteStops(route.stops);
          loadSchedules();
        }}
      />
      <RouteMap stops={latestRouteStops} />

      <div className="flex items-center justify-between">
        <h2 className="text-sm font-semibold text-slate-700">Saved Route Schedules</h2>
        <button onClick={loadSchedules} className="rounded bg-slate-800 px-3 py-2 text-xs text-white">
          Refresh
        </button>
      </div>
      {error ? <p className="text-red-600">{error}</p> : null}
      <RouteSchedulesTable schedules={schedules} />
    </div>
  );
}

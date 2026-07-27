import { useState } from 'react';

import { optimizeRoute } from '../services/logisticsApi';
import type { RouteOptimizeResponse } from '../types/api';

export function RouteOptimizerForm({
  onOptimized,
}: {
  onOptimized?: (route: RouteOptimizeResponse) => void;
}) {
  const [payload, setPayload] = useState({
    route_name: 'Daily Optimized Route',
    schedule_date: new Date().toISOString().slice(0, 10),
    start_warehouse_code: 'WH-001',
    deliveries: 'WH-002:80,WH-003:60',
    vehicle_capacity_units: 180,
    max_stops: 10,
    speed_kmh: 45,
    cost_per_km: 1.5,
    persist_schedule: true,
  });
  const [result, setResult] = useState<RouteOptimizeResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setResult(null);
    setIsSubmitting(true);

    try {
      const deliveries = payload.deliveries
        .split(',')
        .map((chunk) => chunk.trim())
        .filter(Boolean)
        .map((part) => {
          const [warehouse_code, units] = part.split(':');
          return { warehouse_code: warehouse_code.trim(), demand_units: Number(units) };
        });

      const response = await optimizeRoute({
        route_name: payload.route_name,
        schedule_date: payload.schedule_date,
        start_warehouse_code: payload.start_warehouse_code,
        deliveries,
        vehicle_capacity_units: Number(payload.vehicle_capacity_units),
        max_stops: Number(payload.max_stops),
        speed_kmh: Number(payload.speed_kmh),
        cost_per_km: Number(payload.cost_per_km),
        persist_schedule: payload.persist_schedule,
      });

      setResult(response);
      onOptimized?.(response);
    } catch (err: any) {
      setError(err?.response?.data?.detail || err.message || 'Failed to optimize route');
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <div className="rounded-xl bg-white p-4 shadow-sm ring-1 ring-slate-200">
      <h3 className="mb-4 text-sm font-semibold text-slate-700">Optimize Delivery Route</h3>
      <form onSubmit={onSubmit} className="grid grid-cols-1 gap-3 md:grid-cols-2">
        <input className="rounded border px-3 py-2" value={payload.route_name} onChange={(e) => setPayload({ ...payload, route_name: e.target.value })} placeholder="Route name" />
        <input className="rounded border px-3 py-2" type="date" value={payload.schedule_date} onChange={(e) => setPayload({ ...payload, schedule_date: e.target.value })} />
        <input className="rounded border px-3 py-2" value={payload.start_warehouse_code} onChange={(e) => setPayload({ ...payload, start_warehouse_code: e.target.value })} placeholder="Start warehouse code" />
        <input className="rounded border px-3 py-2" value={payload.deliveries} onChange={(e) => setPayload({ ...payload, deliveries: e.target.value })} placeholder="WH-002:80,WH-003:60" />
        <input className="rounded border px-3 py-2" type="number" value={payload.vehicle_capacity_units} onChange={(e) => setPayload({ ...payload, vehicle_capacity_units: Number(e.target.value) })} placeholder="Vehicle capacity" />
        <input className="rounded border px-3 py-2" type="number" value={payload.max_stops} onChange={(e) => setPayload({ ...payload, max_stops: Number(e.target.value) })} placeholder="Max stops" />
        <input className="rounded border px-3 py-2" type="number" step="0.1" value={payload.speed_kmh} onChange={(e) => setPayload({ ...payload, speed_kmh: Number(e.target.value) })} placeholder="Speed km/h" />
        <input className="rounded border px-3 py-2" type="number" step="0.1" value={payload.cost_per_km} onChange={(e) => setPayload({ ...payload, cost_per_km: Number(e.target.value) })} placeholder="Cost per km" />
        <label className="col-span-1 flex items-center gap-2 text-sm text-slate-700 md:col-span-2">
          <input type="checkbox" checked={payload.persist_schedule} onChange={(e) => setPayload({ ...payload, persist_schedule: e.target.checked })} />
          Persist optimized route as schedule
        </label>

        <button disabled={isSubmitting} className="col-span-1 rounded bg-slate-900 px-4 py-2 text-white md:col-span-2">
          {isSubmitting ? 'Optimizing...' : 'Optimize Route'}
        </button>
      </form>

      {error ? <p className="mt-3 text-sm text-red-600">{error}</p> : null}

      {result ? (
        <div className="mt-4 rounded border border-slate-200 p-3">
          <p className="text-sm font-medium">Objective: {result.objective}</p>
          <p className="text-sm">Total distance: {result.total_distance_km} km</p>
          <p className="text-sm">Total cost: ${result.total_cost}</p>
          <p className="text-sm">Estimated duration: {result.estimated_duration_min} min</p>
          <p className="mt-2 text-sm font-medium">Stops:</p>
          <ul className="list-inside list-disc text-sm text-slate-700">
            {result.stops.map((stop) => (
              <li key={stop.sequence}>
                #{stop.sequence} {stop.warehouse_code} ({stop.demand_units} units)
              </li>
            ))}
          </ul>
        </div>
      ) : null}
    </div>
  );
}

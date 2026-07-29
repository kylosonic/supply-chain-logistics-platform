import { useState } from 'react';

import { Panel } from './ui/Panel';
import { StatusBadge } from './ui/StatusBadge';
import { optimizeRoute } from '../services/logisticsApi';
import type { RouteOptimizeResponse } from '../types/api';

export function RouteOptimizerForm({
  onOptimized,
}: {
  onOptimized?: (route: RouteOptimizeResponse) => void;
}) {
  const [previousResult, setPreviousResult] = useState<RouteOptimizeResponse | null>(null);
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

      setPreviousResult(result);
      setResult(response);
      onOptimized?.(response);
    } catch (err: any) {
      setError(err?.response?.data?.detail || err.message || 'Failed to optimize route');
    } finally {
      setIsSubmitting(false);
    }
  }

  const fieldClassName =
    'min-h-12 rounded-2xl border border-slate-700 bg-slate-900/80 px-4 text-sm text-slate-100 outline-none transition focus:border-sky-400/50';
  const previousDistanceDelta = previousResult && result ? result.total_distance_km - previousResult.total_distance_km : null;
  const previousCostDelta = previousResult && result ? result.total_cost - previousResult.total_cost : null;

  return (
    <Panel
      eyebrow="Route model"
      title="Optimize a dispatch scenario"
      description="Compare route assumptions, persist the winning option, and preview the resulting stop sequence without leaving the control surface."
    >
      <form onSubmit={onSubmit} className="grid grid-cols-1 gap-3 lg:grid-cols-2">
        <label className="grid gap-2 text-sm text-slate-300">
          Route name
          <input className={fieldClassName} value={payload.route_name} onChange={(e) => setPayload({ ...payload, route_name: e.target.value })} />
        </label>
        <label className="grid gap-2 text-sm text-slate-300">
          Schedule date
          <input className={fieldClassName} type="date" value={payload.schedule_date} onChange={(e) => setPayload({ ...payload, schedule_date: e.target.value })} />
        </label>
        <label className="grid gap-2 text-sm text-slate-300">
          Start warehouse code
          <input className={fieldClassName} value={payload.start_warehouse_code} onChange={(e) => setPayload({ ...payload, start_warehouse_code: e.target.value })} />
        </label>
        <label className="grid gap-2 text-sm text-slate-300">
          Deliveries
          <input className={fieldClassName} value={payload.deliveries} onChange={(e) => setPayload({ ...payload, deliveries: e.target.value })} placeholder="WH-002:80,WH-003:60" />
        </label>
        <label className="grid gap-2 text-sm text-slate-300">
          Vehicle capacity
          <input className={fieldClassName} type="number" value={payload.vehicle_capacity_units} onChange={(e) => setPayload({ ...payload, vehicle_capacity_units: Number(e.target.value) })} />
        </label>
        <label className="grid gap-2 text-sm text-slate-300">
          Max stops
          <input className={fieldClassName} type="number" value={payload.max_stops} onChange={(e) => setPayload({ ...payload, max_stops: Number(e.target.value) })} />
        </label>
        <label className="grid gap-2 text-sm text-slate-300">
          Speed km/h
          <input className={fieldClassName} type="number" step="0.1" value={payload.speed_kmh} onChange={(e) => setPayload({ ...payload, speed_kmh: Number(e.target.value) })} />
        </label>
        <label className="grid gap-2 text-sm text-slate-300">
          Cost per km
          <input className={fieldClassName} type="number" step="0.1" value={payload.cost_per_km} onChange={(e) => setPayload({ ...payload, cost_per_km: Number(e.target.value) })} />
        </label>

        <label className="col-span-1 flex items-center gap-3 rounded-[22px] border border-slate-800 bg-slate-900/60 px-4 py-4 text-sm text-slate-300 lg:col-span-2">
          <input type="checkbox" checked={payload.persist_schedule} onChange={(e) => setPayload({ ...payload, persist_schedule: e.target.checked })} />
          Persist the optimized route as a saved schedule for the wider team.
        </label>

        <button
          disabled={isSubmitting}
          className="col-span-1 inline-flex min-h-12 items-center justify-center rounded-full bg-gradient-to-r from-sky-300 via-sky-400 to-teal-300 px-4 text-sm font-semibold text-slate-950 transition hover:brightness-105 disabled:cursor-not-allowed disabled:opacity-60 lg:col-span-2"
        >
          {isSubmitting ? 'Optimizing scenario...' : 'Optimize route'}
        </button>
      </form>

      {error ? <p className="mt-4 text-sm text-rose-300">{error}</p> : null}

      {result ? (
        <div className="mt-5 space-y-4 rounded-[24px] border border-slate-800 bg-slate-900/60 p-4">
          <div className="flex flex-wrap items-center gap-2">
            <StatusBadge label={result.objective} tone="info" />
            <StatusBadge label={result.unassigned_deliveries.length === 0 ? 'Fully assigned' : 'Review unassigned'} tone={result.unassigned_deliveries.length === 0 ? 'success' : 'warning'} />
          </div>

          <div className="grid gap-3 md:grid-cols-4">
            <div className="rounded-[20px] border border-slate-800 bg-slate-950/70 p-4">
              <p className="text-xs uppercase tracking-[0.18em] text-slate-500">Distance</p>
              <p className="mt-3 font-['Space_Grotesk'] text-2xl font-semibold text-slate-50">{result.total_distance_km} km</p>
            </div>
            <div className="rounded-[20px] border border-slate-800 bg-slate-950/70 p-4">
              <p className="text-xs uppercase tracking-[0.18em] text-slate-500">Cost</p>
              <p className="mt-3 font-['Space_Grotesk'] text-2xl font-semibold text-slate-50">${result.total_cost}</p>
            </div>
            <div className="rounded-[20px] border border-slate-800 bg-slate-950/70 p-4">
              <p className="text-xs uppercase tracking-[0.18em] text-slate-500">Duration</p>
              <p className="mt-3 font-['Space_Grotesk'] text-2xl font-semibold text-slate-50">{result.estimated_duration_min} min</p>
            </div>
            <div className="rounded-[20px] border border-slate-800 bg-slate-950/70 p-4">
              <p className="text-xs uppercase tracking-[0.18em] text-slate-500">Stops</p>
              <p className="mt-3 font-['Space_Grotesk'] text-2xl font-semibold text-slate-50">{result.stops.length}</p>
            </div>
          </div>

          {previousResult ? (
            <div className="rounded-[20px] border border-slate-800 bg-slate-950/70 px-4 py-3 text-sm text-slate-400">
              Compared with the previous scenario:{' '}
              <span className="font-semibold text-slate-200">
                {previousDistanceDelta == null ? 'N/A' : `${previousDistanceDelta >= 0 ? '+' : ''}${previousDistanceDelta.toFixed(1)} km`}
              </span>
              {' | '}
              <span className="font-semibold text-slate-200">
                {previousCostDelta == null ? 'N/A' : `${previousCostDelta >= 0 ? '+' : ''}$${previousCostDelta.toFixed(2)}`}
              </span>
            </div>
          ) : null}

          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">Stop sequence</p>
            <ul className="mt-3 grid gap-2 text-sm text-slate-300">
              {result.stops.map((stop) => (
                <li key={stop.sequence} className="rounded-[18px] border border-slate-800 bg-slate-950/70 px-4 py-3">
                  #{stop.sequence} {stop.warehouse_code} - {stop.demand_units} units - {stop.leg_distance_km} km leg
                </li>
              ))}
            </ul>
          </div>
        </div>
      ) : null}
    </Panel>
  );
}

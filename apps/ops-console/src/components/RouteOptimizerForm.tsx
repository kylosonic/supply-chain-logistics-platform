import { useState } from 'react';
import { useQueryClient } from '@tanstack/react-query';

import { Panel } from './ui/Panel';
import { StatusBadge } from './ui/StatusBadge';
import { RouteDecisionBrief } from './RouteDecisionBrief';
import { optimizeRoute } from '../services/logisticsApi';
import type { RouteOptimizeResponse } from '../types/api';
import { apiErrorMessage } from '../services/authErrors';

export function RouteOptimizerForm({
  onOptimized,
}: {
  onOptimized?: (route: RouteOptimizeResponse) => void;
}) {
  const queryClient = useQueryClient();
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
    minimize_carbon_footprint: false,
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
        minimize_carbon_footprint: payload.minimize_carbon_footprint,
      });

      setPreviousResult(result);
      setResult(response);
      onOptimized?.(response);
      // m6/activation state reflects without a page reload.
      queryClient.invalidateQueries({ queryKey: ['activation'] });
    } catch (err) {
      setError(apiErrorMessage(err, 'Failed to optimize route'));
    } finally {
      setIsSubmitting(false);
    }
  }

  const fieldClassName = 'fp-input min-h-12';
  const previousDistanceDelta = previousResult && result ? result.total_distance_km - previousResult.total_distance_km : null;
  const previousCostDelta = previousResult && result ? result.total_cost - previousResult.total_cost : null;

  return (
    <Panel
      eyebrow="Route model"
      title="Optimize a dispatch scenario"
      description="Compare route assumptions, persist the winning option, and preview the resulting stop sequence without leaving the control surface."
    >
      <form onSubmit={onSubmit} className="space-y-6">
        <div className="grid grid-cols-1 gap-3 lg:grid-cols-2">
          <p className="col-span-full text-[11px] font-medium tracking-[0.18em] text-slate-500">Scenario identity</p>
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
        </div>

        <div className="grid grid-cols-1 gap-3 lg:grid-cols-2">
          <p className="col-span-full text-[11px] font-medium tracking-[0.18em] text-slate-500">Route shape</p>
          <label className="grid gap-2 text-sm text-slate-300">
            Deliveries
            <input className={fieldClassName} value={payload.deliveries} onChange={(e) => setPayload({ ...payload, deliveries: e.target.value })} placeholder="WH-002:80,WH-003:60" />
            <span className="text-xs font-normal text-slate-500">Up to 200 comma-separated warehouse demand entries.</span>
          </label>
          <label className="grid gap-2 text-sm text-slate-300">
            Vehicle capacity
            <input className={fieldClassName} type="number" min={1} value={payload.vehicle_capacity_units} onChange={(e) => setPayload({ ...payload, vehicle_capacity_units: Number(e.target.value) })} />
          </label>
          <label className="grid gap-2 text-sm text-slate-300">
            Max stops
            <input className={fieldClassName} type="number" min={1} max={100} value={payload.max_stops} onChange={(e) => setPayload({ ...payload, max_stops: Number(e.target.value) })} />
          </label>
        </div>

        <div className="grid grid-cols-1 gap-3 lg:grid-cols-2">
          <p className="col-span-full text-[11px] font-medium tracking-[0.18em] text-slate-500">Operating constraints</p>
          <label className="grid gap-2 text-sm text-slate-300">
            Speed km/h
            <input className={fieldClassName} type="number" step="0.1" value={payload.speed_kmh} onChange={(e) => setPayload({ ...payload, speed_kmh: Number(e.target.value) })} />
          </label>
          <label className="grid gap-2 text-sm text-slate-300">
            Cost per km
            <input className={fieldClassName} type="number" step="0.1" value={payload.cost_per_km} onChange={(e) => setPayload({ ...payload, cost_per_km: Number(e.target.value) })} />
          </label>
        </div>

        <div className="grid grid-cols-1 gap-3 lg:grid-cols-2">
          <p className="col-span-full text-[11px] font-medium tracking-[0.18em] text-slate-500">Persistence options</p>
          <label className="col-span-1 flex items-center gap-3 fp-nested-surface px-4 py-4 text-sm text-slate-300">
            <input type="checkbox" checked={payload.persist_schedule} onChange={(e) => setPayload({ ...payload, persist_schedule: e.target.checked })} />
            Persist the optimized route as a saved schedule for the wider team.
          </label>
          <label className="col-span-1 flex items-center gap-3 fp-nested-surface px-4 py-4 text-sm text-slate-300">
            <input type="checkbox" checked={payload.minimize_carbon_footprint} onChange={(e) => setPayload({ ...payload, minimize_carbon_footprint: e.target.checked })} />
            Minimize Carbon Footprint
          </label>
        </div>

        <button
          disabled={isSubmitting}
          className="glow-ring inline-flex min-h-12 w-full items-center justify-center gap-2 rounded-lg bg-sky-500 px-4 text-sm font-semibold text-slate-950 transition-colors hover:bg-sky-400 disabled:cursor-not-allowed disabled:opacity-60"
        >
          {isSubmitting ? (
            <svg className="animate-spin-slow h-4 w-4" viewBox="0 0 24 24" fill="none"><circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeDasharray="50 20" /></svg>
          ) : null}
          {isSubmitting ? 'Optimizing scenario...' : 'Optimize route'}
        </button>
      </form>

      {error ? <p className="mt-4 text-sm text-rose-300">{error}</p> : null}

      {result ? (
        <div className="animate-slide-up mt-5 space-y-4 fp-nested-surface p-5">
          <div className="flex flex-wrap items-center gap-2">
            <StatusBadge label={result.objective} tone="info" />
            <StatusBadge label={result.unassigned_deliveries.length === 0 ? 'Fully assigned' : 'Review unassigned'} tone={result.unassigned_deliveries.length === 0 ? 'success' : 'warning'} />
            {result.co2_saved_kg && result.co2_saved_kg > 0 ? (
              <StatusBadge label={`${result.co2_saved_kg} kg CO2 Saved`} tone="success" />
            ) : null}
          </div>

          <div className="grid gap-3 md:grid-cols-4">
            {[
              { label: 'Distance', value: `${result.total_distance_km} km` },
              { label: 'Cost', value: `$${result.total_cost}` },
              { label: 'Duration', value: `${result.estimated_duration_min} min` },
              { label: 'Stops', value: String(result.stops.length) },
            ].map((stat) => (
              <div key={stat.label} className="hover-lift fp-nested-surface p-4 transition">
                <p className="text-xs uppercase tracking-wide text-slate-500">{stat.label}</p>
                <p className="mt-3 font-mono text-2xl font-medium tabular-nums text-slate-50">{stat.value}</p>
              </div>
            ))}
          </div>

          {previousResult ? (
            <div className="rounded-[var(--fp-radius-panel)] border border-slate-700/50 bg-slate-900/50 px-4 py-3.5 text-sm text-slate-400">
              Compared with the previous scenario:{' '}
              <span className={`font-mono font-semibold tabular-nums ${previousDistanceDelta != null && previousDistanceDelta < 0 ? 'text-emerald-300' : 'text-slate-200'}`}>
                {previousDistanceDelta == null ? 'N/A' : `${previousDistanceDelta >= 0 ? '+' : ''}${previousDistanceDelta.toFixed(1)} km`}
              </span>
              {' | '}
              <span className={`font-mono font-semibold tabular-nums ${previousCostDelta != null && previousCostDelta < 0 ? 'text-emerald-300' : 'text-slate-200'}`}>
                {previousCostDelta == null ? 'N/A' : `${previousCostDelta >= 0 ? '+' : ''}$${previousCostDelta.toFixed(2)}`}
              </span>
            </div>
          ) : null}

          <RouteDecisionBrief explanation={result.decision_explanation} />

          <div>
            <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Stop sequence</p>
            <ul className="mt-3 grid gap-1.5 text-sm text-slate-300">
              {result.stops.map((stop) => (
                <li key={stop.sequence} className="fp-row px-4 py-2.5">
                  <span className="font-semibold text-slate-100">#{stop.sequence}</span> {stop.warehouse_code} · {stop.demand_units} units · {stop.leg_distance_km} km leg
                </li>
              ))}
            </ul>
          </div>
        </div>
      ) : null}
    </Panel>
  );
}


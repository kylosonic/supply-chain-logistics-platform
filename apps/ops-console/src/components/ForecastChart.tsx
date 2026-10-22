import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';

import { Panel } from './ui/Panel';
import type { ForecastPoint, ForecastQuality } from '../types/api';

type Props = {
  points: ForecastPoint[];
  quality?: ForecastQuality | null;
  modelName?: string;
};

const axisStyle = { fill: '#94a3b8', fontSize: 12 };
const tooltipStyle = {
  backgroundColor: '#020817',
  border: '1px solid rgba(148, 163, 184, 0.22)',
  borderRadius: '16px',
  color: '#e2e8f0',
};

export function ForecastChart({ points, quality, modelName }: Props) {
  const grouped = new Map<
    string,
    { predicted_total_demand: number; planning_low: number; planning_high: number }
  >();
  points.forEach((point) => {
    const key = point.week_start;
    const current = grouped.get(key) ?? {
      predicted_total_demand: 0,
      planning_low: 0,
      planning_high: 0,
    };
    grouped.set(key, {
      predicted_total_demand: current.predicted_total_demand + point.predicted_demand,
      planning_low: current.planning_low + point.planning_low,
      planning_high: current.planning_high + point.planning_high,
    });
  });

  const data = Array.from(grouped.entries())
    .map(([week_start, totals]) => ({ week_start, ...totals }))
    .sort((a, b) => a.week_start.localeCompare(b.week_start));

  const backtestLabel = quality?.wape_percent != null ? `${quality.wape_percent}% WAPE` : 'Not available';
  const hasHighError = quality?.wape_percent != null && quality.wape_percent > 35;
  const qualityTone =
    hasHighError || quality?.status === 'limited'
      ? 'border-amber-500/30 bg-amber-950/15 text-amber-200'
      : quality?.status === 'validated'
        ? 'border-emerald-500/30 bg-emerald-950/15 text-emerald-200'
        : 'border-slate-700/60 bg-slate-900/45 text-slate-300';
  const evidenceLabel = quality
    ? `${quality.status.split('_').join(' ')}${hasHighError ? ' - high error' : ''}`
    : 'Unavailable';
  const widensByBacktest = quality?.range_basis.includes('holdout_error') ?? false;

  return (
    <Panel
      eyebrow="Demand intelligence"
      title="Predicted Weekly Demand"
      description="Point demand, a planning range derived from the available model evidence, and the limits behind the output."
    >
      <div className="mb-5 grid gap-2 sm:grid-cols-2 xl:grid-cols-4">
        <div className="fp-nested-surface px-4 py-3">
          <p className="text-[11px] uppercase tracking-wide text-slate-500">Model</p>
          <p className="mt-1 text-sm font-semibold text-slate-100">{modelName ?? 'Demand model'}</p>
        </div>
        <div className="fp-nested-surface px-4 py-3">
          <p className="text-[11px] uppercase tracking-wide text-slate-500">Backtest error</p>
          <p className="mt-1 font-mono text-sm font-semibold tabular-nums text-slate-100">{backtestLabel}</p>
        </div>
        <div className="fp-nested-surface px-4 py-3">
          <p className="text-[11px] uppercase tracking-wide text-slate-500">Demand history</p>
          <p className="mt-1 font-mono text-sm font-semibold tabular-nums text-slate-100">
            {quality ? `${quality.history_weeks} wk` : 'Unknown'}
          </p>
        </div>
        <div className={`rounded-[var(--fp-radius-panel)] border px-4 py-3 ${qualityTone}`}>
          <p className="text-[11px] uppercase tracking-wide opacity-70">Forecast evidence</p>
          <p className="mt-1 text-sm font-semibold capitalize">{evidenceLabel}</p>
        </div>
      </div>
      <div className="h-80">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={data}>
            <defs>
              <linearGradient id="demandGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#38bdf8" stopOpacity={0.3} />
                <stop offset="100%" stopColor="#38bdf8" stopOpacity={0.02} />
              </linearGradient>
            </defs>
            <CartesianGrid stroke="rgba(148, 163, 184, 0.08)" strokeDasharray="3 3" />
            <XAxis dataKey="week_start" tick={axisStyle} axisLine={false} tickLine={false} />
            <YAxis tick={axisStyle} axisLine={false} tickLine={false} />
            <Tooltip contentStyle={tooltipStyle} cursor={{ stroke: 'rgba(148, 163, 184, 0.18)' }} />
            <Legend wrapperStyle={{ color: '#cbd5e1', fontSize: 12 }} />
            <Line
              type="monotone"
              dataKey="planning_low"
              name="Planning low"
              stroke="#f59e0b"
              strokeWidth={1.5}
              strokeDasharray="5 5"
              dot={false}
              animationDuration={900}
            />
            <Line
              type="monotone"
              dataKey="planning_high"
              name="Planning high"
              stroke="#f59e0b"
              strokeWidth={1.5}
              strokeDasharray="5 5"
              dot={false}
              animationDuration={900}
            />
            <Line
              type="monotone"
              dataKey="predicted_total_demand"
              name="Predicted demand"
              stroke="#38bdf8"
              strokeWidth={2.5}
              dot={false}
              activeDot={{ r: 5, fill: '#38bdf8', stroke: '#0c4a6e', strokeWidth: 2 }}
              animationDuration={1200}
              animationEasing="ease-out"
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
      {quality ? (
        <div className="mt-4 rounded-[var(--fp-radius-panel)] border border-slate-800/70 bg-slate-900/35 px-4 py-3">
          <p className="text-sm leading-6 text-slate-300">{quality.interpretation}</p>
          <p className="mt-1 text-xs leading-5 text-slate-500">{quality.caveat}</p>
          <p className="mt-1 text-xs leading-5 text-slate-500">
            {widensByBacktest
              ? 'Planning range widens ensemble spread by held-out error; it is not a guarantee.'
              : 'Planning range reflects ensemble spread only; no held-out error estimate was available.'}
          </p>
        </div>
      ) : null}
    </Panel>
  );
}

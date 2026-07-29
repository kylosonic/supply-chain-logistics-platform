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

import type { ForecastPoint } from '../types/api';

type Props = {
  points: ForecastPoint[];
};

const axisStyle = { fill: '#94a3b8', fontSize: 12 };
const tooltipStyle = {
  backgroundColor: '#020817',
  border: '1px solid rgba(148, 163, 184, 0.22)',
  borderRadius: '16px',
  color: '#e2e8f0',
};

export function ForecastChart({ points }: Props) {
  const grouped = new Map<string, number>();
  points.forEach((point) => {
    const key = point.week_start;
    grouped.set(key, (grouped.get(key) ?? 0) + point.predicted_demand);
  });

  const data = Array.from(grouped.entries())
    .map(([week_start, predicted_total_demand]) => ({ week_start, predicted_total_demand }))
    .sort((a, b) => a.week_start.localeCompare(b.week_start));

  return (
    <div className="rounded-[28px] border border-slate-800/80 bg-slate-950/72 p-5 shadow-[0_24px_80px_rgba(2,12,20,0.3)]">
      <h3 className="mb-4 font-['Space_Grotesk'] text-lg font-semibold text-slate-50">Predicted Weekly Demand</h3>
      <div className="h-80">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={data}>
            <CartesianGrid stroke="rgba(148, 163, 184, 0.12)" strokeDasharray="3 3" />
            <XAxis dataKey="week_start" tick={axisStyle} axisLine={false} tickLine={false} />
            <YAxis tick={axisStyle} axisLine={false} tickLine={false} />
            <Tooltip contentStyle={tooltipStyle} cursor={{ stroke: 'rgba(148, 163, 184, 0.18)' }} />
            <Legend wrapperStyle={{ color: '#cbd5e1', fontSize: 12 }} />
            <Line type="monotone" dataKey="predicted_total_demand" stroke="#ef4444" strokeWidth={3} dot={false} />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

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
    <div className="rounded-xl bg-white p-4 shadow-sm ring-1 ring-slate-200">
      <h3 className="mb-4 text-sm font-semibold text-slate-700">Predicted Weekly Demand (Aggregated)</h3>
      <div className="h-80">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={data}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="week_start" />
            <YAxis />
            <Tooltip />
            <Legend />
            <Line type="monotone" dataKey="predicted_total_demand" stroke="#ef4444" strokeWidth={3} dot={false} />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

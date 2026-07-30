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
    <Panel
      eyebrow="Demand intelligence"
      title="Predicted Weekly Demand"
      description="Aggregated demand forecast across all tracked SKUs for the planning horizon."
    >
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
    </Panel>
  );
}

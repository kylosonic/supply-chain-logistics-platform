import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';

import type { InventoryOverviewRow } from '../types/api';

const COLORS = ['#0ea5e9', '#6366f1', '#22c55e', '#f59e0b', '#ef4444', '#8b5cf6'];

const axisStyle = { fill: '#94a3b8', fontSize: 12 };
const tooltipStyle = {
  backgroundColor: '#020817',
  border: '1px solid rgba(148, 163, 184, 0.22)',
  borderRadius: '16px',
  color: '#e2e8f0',
};

type Props = {
  data: InventoryOverviewRow[];
};

export function InventoryCharts({ data }: Props) {
  return (
    <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
      <div className="rounded-[28px] border border-slate-800/80 bg-slate-950/72 p-5 shadow-[0_24px_80px_rgba(2,12,20,0.3)]">
        <h3 className="mb-4 font-['Space_Grotesk'] text-lg font-semibold text-slate-50">Stock by Warehouse</h3>
        <div className="h-72">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={data}>
              <CartesianGrid stroke="rgba(148, 163, 184, 0.12)" strokeDasharray="3 3" />
              <XAxis dataKey="warehouse_code" tick={axisStyle} axisLine={false} tickLine={false} />
              <YAxis tick={axisStyle} axisLine={false} tickLine={false} />
              <Tooltip contentStyle={tooltipStyle} cursor={{ fill: 'rgba(148, 163, 184, 0.06)' }} />
              <Legend wrapperStyle={{ color: '#cbd5e1', fontSize: 12 }} />
              <Bar dataKey="total_quantity_on_hand" name="Quantity On Hand" fill="#0ea5e9" />
              <Bar dataKey="total_safety_stock" name="Safety Stock" fill="#6366f1" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="rounded-[28px] border border-slate-800/80 bg-slate-950/72 p-5 shadow-[0_24px_80px_rgba(2,12,20,0.3)]">
        <h3 className="mb-4 font-['Space_Grotesk'] text-lg font-semibold text-slate-50">Capacity Utilization</h3>
        <div className="h-72">
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie
                data={data}
                dataKey="utilization_percent"
                nameKey="warehouse_code"
                outerRadius={100}
                label={(entry) => `${entry.warehouse_code}: ${entry.utilization_percent}%`}
              >
                {data.map((_, index) => (
                  <Cell key={index} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip contentStyle={tooltipStyle} />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
}

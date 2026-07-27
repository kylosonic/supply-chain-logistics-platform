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

type Props = {
  data: InventoryOverviewRow[];
};

export function InventoryCharts({ data }: Props) {
  return (
    <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
      <div className="rounded-xl bg-white p-4 shadow-sm ring-1 ring-slate-200">
        <h3 className="mb-4 text-sm font-semibold text-slate-700">Stock by Warehouse</h3>
        <div className="h-72">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={data}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="warehouse_code" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Bar dataKey="total_quantity_on_hand" name="Quantity On Hand" fill="#0ea5e9" />
              <Bar dataKey="total_safety_stock" name="Safety Stock" fill="#6366f1" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="rounded-xl bg-white p-4 shadow-sm ring-1 ring-slate-200">
        <h3 className="mb-4 text-sm font-semibold text-slate-700">Capacity Utilization %</h3>
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
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
}

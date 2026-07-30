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

import { Panel } from './ui/Panel';
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
    <div className="grid grid-cols-1 gap-5 lg:grid-cols-2">
      <Panel
        eyebrow="Inventory intelligence"
        title="Stock by Warehouse"
        description="On-hand quantity versus safety stock levels across active warehouse locations."
      >
        <div className="h-72">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={data} barCategoryGap="18%">
              <CartesianGrid stroke="rgba(148, 163, 184, 0.08)" strokeDasharray="3 3" />
              <XAxis dataKey="warehouse_code" tick={axisStyle} axisLine={false} tickLine={false} />
              <YAxis tick={axisStyle} axisLine={false} tickLine={false} />
              <Tooltip contentStyle={tooltipStyle} cursor={{ fill: 'rgba(148, 163, 184, 0.06)' }} />
              <Legend wrapperStyle={{ color: '#cbd5e1', fontSize: 12 }} />
              <Bar
                dataKey="total_quantity_on_hand"
                name="Quantity On Hand"
                fill="#0ea5e9"
                radius={[6, 6, 0, 0]}
                animationDuration={1000}
              />
              <Bar
                dataKey="total_safety_stock"
                name="Safety Stock"
                fill="#6366f1"
                radius={[6, 6, 0, 0]}
                animationDuration={1200}
              />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </Panel>

      <Panel
        eyebrow="Capacity view"
        title="Warehouse Utilization"
        description="Capacity utilization percentage across tracked warehouse locations."
      >
        <div className="h-72">
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie
                data={data}
                dataKey="utilization_percent"
                nameKey="warehouse_code"
                innerRadius={55}
                outerRadius={100}
                paddingAngle={3}
                label={(entry) => `${entry.warehouse_code}: ${entry.utilization_percent}%`}
                animationDuration={1200}
                animationEasing="ease-out"
              >
                {data.map((_, index) => (
                  <Cell key={index} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip contentStyle={tooltipStyle} />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </Panel>
    </div>
  );
}

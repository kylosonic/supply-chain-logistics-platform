import { StatusBadge } from './ui/StatusBadge';
import type { RouteScheduleSummary } from '../types/api';

type Props = {
  schedules: RouteScheduleSummary[];
};

function scheduleTone(status: string) {
  if (status === 'completed' || status === 'delivered') return 'success';
  if (status === 'delayed' || status === 'failed') return 'danger';
  if (status === 'active' || status === 'in_progress') return 'warning';
  return 'neutral';
}

export function RouteSchedulesTable({ schedules }: Props) {
  return (
    <div className="overflow-x-auto rounded-[22px] border border-slate-800 bg-slate-900/60">
      <table className="min-w-full divide-y divide-slate-800 text-sm">
        <thead className="bg-slate-950/80">
          <tr>
            <th className="px-4 py-3 text-left font-medium text-slate-400">Route</th>
            <th className="px-4 py-3 text-left font-medium text-slate-400">Date</th>
            <th className="px-4 py-3 text-left font-medium text-slate-400">Distance (km)</th>
            <th className="px-4 py-3 text-left font-medium text-slate-400">Cost</th>
            <th className="px-4 py-3 text-left font-medium text-slate-400">Duration (min)</th>
            <th className="px-4 py-3 text-left font-medium text-slate-400">Status</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-800 bg-transparent">
          {schedules.map((route) => (
            <tr key={route.id}>
              <td className="px-4 py-3 text-slate-100">{route.route_name}</td>
              <td className="px-4 py-3 text-slate-300">{route.schedule_date}</td>
              <td className="px-4 py-3 text-slate-300">{route.total_distance_km}</td>
              <td className="px-4 py-3 text-slate-300">${route.total_cost}</td>
              <td className="px-4 py-3 text-slate-300">{route.estimated_duration_min}</td>
              <td className="px-4 py-3 text-slate-300">
                <StatusBadge label={route.status} tone={scheduleTone(route.status)} />
              </td>
            </tr>
          ))}
          {schedules.length === 0 ? (
            <tr>
              <td colSpan={6} className="px-4 py-10 text-center text-slate-500">
                No route schedules saved yet.
              </td>
            </tr>
          ) : null}
        </tbody>
      </table>
    </div>
  );
}

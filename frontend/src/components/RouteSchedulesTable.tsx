import type { RouteScheduleSummary } from '../types/api';

type Props = {
  schedules: RouteScheduleSummary[];
};

export function RouteSchedulesTable({ schedules }: Props) {
  return (
    <div className="overflow-x-auto rounded-xl bg-white shadow-sm ring-1 ring-slate-200">
      <table className="min-w-full divide-y divide-slate-200 text-sm">
        <thead className="bg-slate-50">
          <tr>
            <th className="px-4 py-3 text-left font-medium text-slate-600">Route</th>
            <th className="px-4 py-3 text-left font-medium text-slate-600">Date</th>
            <th className="px-4 py-3 text-left font-medium text-slate-600">Distance (km)</th>
            <th className="px-4 py-3 text-left font-medium text-slate-600">Cost</th>
            <th className="px-4 py-3 text-left font-medium text-slate-600">Duration (min)</th>
            <th className="px-4 py-3 text-left font-medium text-slate-600">Status</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-100 bg-white">
          {schedules.map((route) => (
            <tr key={route.id}>
              <td className="px-4 py-3 text-slate-900">{route.route_name}</td>
              <td className="px-4 py-3 text-slate-700">{route.schedule_date}</td>
              <td className="px-4 py-3 text-slate-700">{route.total_distance_km}</td>
              <td className="px-4 py-3 text-slate-700">${route.total_cost}</td>
              <td className="px-4 py-3 text-slate-700">{route.estimated_duration_min}</td>
              <td className="px-4 py-3 text-slate-700">
                <span className="rounded bg-slate-100 px-2 py-1 text-xs">{route.status}</span>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

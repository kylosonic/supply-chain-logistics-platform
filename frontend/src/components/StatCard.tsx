type StatCardProps = {
  title: string;
  value: string | number;
  subtitle?: string;
};

export function StatCard({ title, value, subtitle }: StatCardProps) {
  return (
    <div className="rounded-xl bg-white p-4 shadow-sm ring-1 ring-slate-200">
      <p className="text-sm text-slate-600">{title}</p>
      <p className="mt-2 text-2xl font-semibold text-slate-900">{value}</p>
      {subtitle ? <p className="mt-1 text-xs text-slate-500">{subtitle}</p> : null}
    </div>
  );
}

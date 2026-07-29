type StatusTone = 'neutral' | 'info' | 'success' | 'warning' | 'danger';

type StatusBadgeProps = {
  label: string;
  tone?: StatusTone;
};

const toneClasses: Record<StatusTone, string> = {
  neutral: 'border-slate-700 bg-slate-900 text-slate-200',
  info: 'border-sky-500/30 bg-sky-950/40 text-sky-200',
  success: 'border-emerald-500/30 bg-emerald-950/40 text-emerald-200',
  warning: 'border-amber-500/30 bg-amber-950/40 text-amber-200',
  danger: 'border-rose-500/30 bg-rose-950/40 text-rose-200',
};

export function StatusBadge({ label, tone = 'neutral' }: StatusBadgeProps) {
  return (
    <span
      className={`inline-flex items-center rounded-full border px-2.5 py-1 text-[11px] font-semibold uppercase tracking-[0.18em] ${toneClasses[tone]}`}
    >
      {label}
    </span>
  );
}
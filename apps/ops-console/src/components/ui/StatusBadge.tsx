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

const dotColors: Record<StatusTone, string> = {
  neutral: 'bg-slate-400',
  info: 'bg-sky-400',
  success: 'bg-emerald-400',
  warning: 'bg-amber-400',
  danger: 'bg-rose-400',
};

export function StatusBadge({ label, tone = 'neutral' }: StatusBadgeProps) {
  const isPulsing = tone === 'danger' || tone === 'warning';

  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-[11px] font-semibold uppercase tracking-[0.18em] ${toneClasses[tone]}`}
    >
      <span
        className={`inline-block h-1.5 w-1.5 rounded-full ${dotColors[tone]}`}
        style={isPulsing ? { animation: 'pulseRing 2s ease-in-out infinite' } : undefined}
      />
      {label}
    </span>
  );
}
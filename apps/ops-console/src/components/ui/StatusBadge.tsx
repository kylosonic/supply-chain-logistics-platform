type StatusTone = 'neutral' | 'info' | 'success' | 'warning' | 'danger';

type StatusBadgeProps = {
  label: string;
  tone?: StatusTone;
};

const toneClasses: Record<StatusTone, string> = {
  neutral: 'border-slate-700/60 bg-slate-900 text-slate-300',
  info: 'border-sky-500/25 bg-sky-950/30 text-sky-300',
  success: 'border-emerald-500/25 bg-emerald-950/30 text-emerald-300',
  warning: 'border-amber-500/25 bg-amber-950/30 text-amber-300',
  danger: 'border-rose-500/25 bg-rose-950/30 text-rose-300',
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
      className={`inline-flex items-center gap-1.5 rounded-md border px-2 py-0.5 text-[11px] font-medium uppercase tracking-wide ${toneClasses[tone]}`}
    >
      <span
        className={`inline-block h-1.5 w-1.5 rounded-full ${dotColors[tone]}`}
        style={isPulsing ? { animation: 'pulseRing 2s ease-in-out infinite' } : undefined}
      />
      {label}
    </span>
  );
}

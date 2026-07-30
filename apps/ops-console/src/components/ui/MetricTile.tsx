type MetricTone = 'neutral' | 'success' | 'warning' | 'danger' | 'info';

type MetricTileProps = {
  title: string;
  value: string | number;
  detail: string;
  tone?: MetricTone;
};

const toneClasses: Record<MetricTone, string> = {
  neutral: 'border-slate-800/80 bg-slate-950/72',
  success: 'border-emerald-500/25 bg-emerald-950/20',
  warning: 'border-amber-500/25 bg-amber-950/20',
  danger: 'border-rose-500/25 bg-rose-950/20',
  info: 'border-sky-500/25 bg-sky-950/20',
};

const dotColors: Record<MetricTone, string> = {
  neutral: 'bg-slate-500',
  success: 'bg-emerald-400',
  warning: 'bg-amber-400',
  danger: 'bg-rose-400',
  info: 'bg-sky-400',
};

export function MetricTile({ title, value, detail, tone = 'neutral' }: MetricTileProps) {
  return (
    <article
      className={`hover-lift top-highlight animate-scale-in rounded-[24px] border px-5 py-5 shadow-[0_18px_48px_rgba(2,12,20,0.22)] ${toneClasses[tone]}`}
    >
      <div className="flex items-center gap-2">
        <span className={`inline-block h-1.5 w-1.5 rounded-full ${dotColors[tone]}`} style={{ animation: tone === 'danger' || tone === 'warning' ? 'pulseRing 2s ease-in-out infinite' : 'none' }} />
        <p className="text-xs font-semibold uppercase tracking-[0.2em] text-slate-400">{title}</p>
      </div>
      <p className="mt-3 font-['Space_Grotesk'] text-3xl font-semibold tabular-nums text-slate-50">{value}</p>
      <p className="mt-2 text-sm leading-6 text-slate-400">{detail}</p>
    </article>
  );
}
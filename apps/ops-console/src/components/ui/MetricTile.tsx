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

export function MetricTile({ title, value, detail, tone = 'neutral' }: MetricTileProps) {
  return (
    <article
      className={`rounded-[24px] border px-5 py-5 shadow-[0_18px_48px_rgba(2,12,20,0.22)] ${toneClasses[tone]}`}
    >
      <p className="text-xs font-semibold uppercase tracking-[0.2em] text-slate-400">{title}</p>
      <p className="mt-3 font-['Space_Grotesk'] text-3xl font-semibold text-slate-50">{value}</p>
      <p className="mt-2 text-sm leading-6 text-slate-400">{detail}</p>
    </article>
  );
}
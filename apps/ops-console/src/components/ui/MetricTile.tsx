import { Link } from 'react-router-dom';

type MetricTone = 'neutral' | 'success' | 'warning' | 'danger' | 'info';

type MetricTileProps = {
  title: string;
  value: string | number;
  detail: string;
  tone?: MetricTone;
  cta?: { label: string; href: string };
};

const dotColors: Record<MetricTone, string> = {
  neutral: 'bg-slate-500',
  success: 'bg-emerald-400',
  warning: 'bg-amber-400',
  danger: 'bg-rose-400',
  info: 'bg-sky-400',
};

export function MetricTile({ title, value, detail, tone = 'neutral', cta }: MetricTileProps) {
  const isPulsing = tone === 'danger' || tone === 'warning';

  return (
    <article className="hover-lift animate-scale-in rounded-xl border border-slate-800/60 bg-slate-900/40 px-4 py-4">
      <div className="flex items-center gap-2">
        <span
          className={`inline-block h-1.5 w-1.5 rounded-full ${dotColors[tone]}`}
          style={isPulsing ? { animation: 'pulseRing 2s ease-in-out infinite' } : undefined}
        />
        <p className="text-xs font-medium text-slate-500">{title}</p>
      </div>
      <p className="mt-2 font-mono text-2xl font-medium tabular-nums tracking-tight text-slate-100">{value}</p>
      <p className="mt-1.5 text-sm leading-5 text-slate-400">{detail}</p>
      {cta ? (
        // NB-54: internal CTA targets (leading "/") navigate via the router
        // — never a browser reload; anything else stays an external anchor.
        cta.href.startsWith('/') ? (
          <Link to={cta.href} className="mt-2 inline-block text-sm font-medium text-sky-400 underline-offset-4 hover:underline">
            {cta.label} →
          </Link>
        ) : (
          <a href={cta.href} className="mt-2 inline-block text-sm font-medium text-sky-400 underline-offset-4 hover:underline">
            {cta.label} →
          </a>
        )
      ) : null}
    </article>
  );
}

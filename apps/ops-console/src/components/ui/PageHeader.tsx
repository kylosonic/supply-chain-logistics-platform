import type { ReactNode } from 'react';

type PageHeaderProps = {
  eyebrow?: string;
  title: string;
  description: string;
  actions?: ReactNode;
};

export function PageHeader({ eyebrow, title, description, actions }: PageHeaderProps) {
  return (
    <section className="animate-slide-up top-highlight overflow-hidden rounded-[30px] border border-slate-800/80 bg-[radial-gradient(circle_at_top_right,_rgba(56,189,248,0.16),_transparent_24%),linear-gradient(160deg,rgba(6,14,21,0.96),rgba(11,29,40,0.92))] px-6 py-6 shadow-[0_24px_80px_rgba(2,12,20,0.38)]">
      <div className="flex flex-wrap items-start justify-between gap-5">
        <div className="max-w-3xl space-y-2">
          {eyebrow ? <p className="text-xs font-semibold uppercase tracking-[0.24em] text-sky-300/80">{eyebrow}</p> : null}
          <h1 className="font-['Space_Grotesk'] text-[clamp(2rem,3vw,3rem)] font-semibold leading-none text-slate-50">
            {title}
          </h1>
          <p className="max-w-3xl text-sm leading-6 text-slate-300">{description}</p>
        </div>
        {actions ? <div className="flex flex-wrap items-center gap-2">{actions}</div> : null}
      </div>
    </section>
  );
}
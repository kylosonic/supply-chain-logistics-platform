import type { ReactNode } from 'react';

type PageHeaderProps = {
  eyebrow?: string;
  title: string;
  description: string;
  actions?: ReactNode;
};

export function PageHeader({ eyebrow, title, description, actions }: PageHeaderProps) {
  return (
    <section className="fp-shell-surface px-5 py-5 sm:px-6 sm:py-6">
      <div className="flex flex-wrap items-start justify-between gap-5 lg:gap-6">
        <div className="max-w-3xl space-y-2">
          {eyebrow ? <p className="text-[11px] font-medium tracking-[0.18em] text-slate-500">{eyebrow}</p> : null}
          <h1 className="font-['Space_Grotesk'] text-[clamp(1.65rem,2.4vw,2.25rem)] font-semibold tracking-tight text-slate-100">
            {title}
          </h1>
          <p className="max-w-3xl text-sm leading-7 text-slate-400">{description}</p>
        </div>
        {actions ? <div className="flex flex-wrap items-center gap-2.5">{actions}</div> : null}
      </div>
    </section>
  );
}

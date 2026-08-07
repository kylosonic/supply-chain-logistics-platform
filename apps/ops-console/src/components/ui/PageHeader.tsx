import type { ReactNode } from 'react';

type PageHeaderProps = {
  eyebrow?: string;
  title: string;
  description: string;
  actions?: ReactNode;
};

export function PageHeader({ eyebrow, title, description, actions }: PageHeaderProps) {
  return (
    <section className="animate-slide-up border-b border-slate-800/60 px-1 pb-5 pt-1">
      <div className="flex flex-wrap items-start justify-between gap-5">
        <div className="max-w-3xl space-y-1.5">
          {eyebrow ? <p className="text-xs font-medium text-slate-500">{eyebrow}</p> : null}
          <h1 className="font-['Space_Grotesk'] text-2xl font-semibold tracking-tight text-slate-100">
            {title}
          </h1>
          <p className="max-w-3xl text-sm leading-6 text-slate-400">{description}</p>
        </div>
        {actions ? <div className="flex flex-wrap items-center gap-2">{actions}</div> : null}
      </div>
    </section>
  );
}

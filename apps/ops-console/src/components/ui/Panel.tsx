import type { PropsWithChildren, ReactNode } from 'react';

type PanelProps = PropsWithChildren<{
  eyebrow?: string;
  title?: string;
  description?: string;
  actions?: ReactNode;
  className?: string;
  bodyClassName?: string;
}>;

function joinClasses(...parts: Array<string | undefined>) {
  return parts.filter(Boolean).join(' ');
}

export function Panel({ eyebrow, title, description, actions, className, bodyClassName, children }: PanelProps) {
  const hasHeader = eyebrow || title || description || actions;

  return (
    <section
      className={joinClasses(
        'animate-fade-in top-highlight overflow-hidden rounded-[28px] border border-slate-800/80 bg-slate-950/72 shadow-[0_24px_80px_rgba(2,12,20,0.34)] backdrop-blur',
        className,
      )}
    >
      {hasHeader ? (
        <header className="flex flex-wrap items-start justify-between gap-4 border-b border-slate-800/60 bg-gradient-to-r from-transparent via-slate-900/20 to-transparent px-5 py-5">
          <div className="max-w-3xl space-y-2">
            {eyebrow ? <p className="text-xs font-semibold uppercase tracking-[0.24em] text-sky-300/80">{eyebrow}</p> : null}
            {title ? <h2 className="font-['Space_Grotesk'] text-xl font-semibold text-slate-50">{title}</h2> : null}
            {description ? <p className="text-sm leading-6 text-slate-400">{description}</p> : null}
          </div>
          {actions ? <div className="flex flex-wrap items-center gap-2">{actions}</div> : null}
        </header>
      ) : null}

      <div className={joinClasses('px-5 py-5', bodyClassName)}>{children}</div>
    </section>
  );
}
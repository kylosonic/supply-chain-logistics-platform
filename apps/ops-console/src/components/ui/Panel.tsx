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
        'fp-nested-surface animate-fade-in overflow-hidden',
        className,
      )}
    >
      {hasHeader ? (
        <header className="flex flex-wrap items-start justify-between gap-4 border-b border-slate-800/70 px-5 py-4">
          <div className="max-w-3xl space-y-1.5">
            {eyebrow ? <p className="text-[11px] font-medium tracking-[0.18em] text-slate-500">{eyebrow}</p> : null}
            {title ? <h2 className="font-['Space_Grotesk'] text-lg font-semibold tracking-tight text-slate-100">{title}</h2> : null}
            {description ? <p className="text-sm leading-6 text-slate-400">{description}</p> : null}
          </div>
          {actions ? <div className="flex flex-wrap items-center gap-2.5">{actions}</div> : null}
        </header>
      ) : null}

      <div className={joinClasses('px-5 py-5', bodyClassName)}>{children}</div>
    </section>
  );
}

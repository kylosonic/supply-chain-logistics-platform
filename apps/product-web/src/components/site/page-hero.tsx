import type { ReactNode } from 'react';

type PageHeroProps = {
  eyebrow: string;
  title: string;
  description: string;
  actions?: ReactNode;
  aside?: ReactNode;
};

export function PageHero({ eyebrow, title, description, actions, aside }: PageHeroProps) {
  return (
    <section className="section-shell pt-6 sm:pt-10 lg:pt-12">
      <div className="glass-panel grid gap-6 overflow-hidden rounded-[32px] px-5 py-6 sm:gap-8 sm:px-8 sm:py-8 lg:grid-cols-[1.04fr_0.96fr] lg:gap-8 lg:px-10 lg:py-10 xl:gap-10">
        <div className="space-y-4 sm:space-y-5">
          <p className="kicker">{eyebrow}</p>
          <h1 className="balanced-headline max-w-[10ch] font-display text-[clamp(2.55rem,5.5vw,4.85rem)] leading-[0.94] tracking-[-0.03em] text-white">{title}</h1>
          <p className="lede text-[0.98rem] sm:text-base">{description}</p>
          {actions ? <div className="flex flex-col items-stretch gap-3 pt-3 sm:flex-row sm:flex-wrap sm:items-center [&>*]:w-full sm:[&>*]:w-auto">{actions}</div> : null}
        </div>
        {aside ? <div className="relative lg:pt-2">{aside}</div> : null}
      </div>
    </section>
  );
}
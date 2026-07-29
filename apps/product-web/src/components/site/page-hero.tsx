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
      <div className="glass-panel grid gap-6 overflow-hidden rounded-[32px] px-5 py-6 sm:gap-8 sm:px-8 sm:py-8 lg:grid-cols-[1.12fr_0.88fr] lg:gap-10 lg:px-10 lg:py-10">
        <div className="space-y-4 sm:space-y-5">
          <p className="kicker">{eyebrow}</p>
          <h1 className="balanced-headline max-w-[11ch] font-display text-[clamp(2.85rem,6vw,5.4rem)] leading-[0.92] tracking-[-0.035em] text-white">{title}</h1>
          <p className="max-w-[38rem] text-base leading-8 text-white/68">{description}</p>
          {actions ? <div className="flex flex-col items-stretch gap-3 pt-3 sm:flex-row sm:flex-wrap sm:items-center [&>*]:w-full sm:[&>*]:w-auto">{actions}</div> : null}
        </div>
        {aside ? <div className="relative lg:pt-2">{aside}</div> : null}
      </div>
    </section>
  );
}
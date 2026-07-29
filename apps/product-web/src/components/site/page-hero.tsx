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
    <section className="section-shell pt-10 sm:pt-16">
      <div className="glass-panel grid gap-8 overflow-hidden rounded-[36px] px-6 py-8 sm:px-8 sm:py-10 lg:grid-cols-[1.08fr_0.92fr]">
        <div className="space-y-5">
          <p className="kicker">{eyebrow}</p>
          <h1 className="font-display text-[clamp(2.7rem,6vw,5.7rem)] leading-[0.92] text-white">{title}</h1>
          <p className="max-w-2xl text-base leading-8 text-white/68">{description}</p>
          {actions ? <div className="flex flex-wrap gap-3 pt-2">{actions}</div> : null}
        </div>
        {aside ? <div className="relative">{aside}</div> : null}
      </div>
    </section>
  );
}
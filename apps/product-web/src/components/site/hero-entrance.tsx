'use client';

import { m } from 'framer-motion';

import { heroHeadline } from '@/lib/site-content';

/**
 * The home page's single allowed entrance animation (NB-42.5 / blueprint
 * §1.3): a mount-time fade+rise on the hero headline. No whileInView, no
 * repeat. Extracted to a client component so the server page never touches
 * framer-motion's module proxy at prerender time.
 */
export function HeroEntrance() {
  return (
    <m.h1
      data-hero-entrance
      initial={{ opacity: 0, y: 24 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.6, ease: [0.16, 1, 0.3, 1] }}
      className="balanced-headline max-w-[18ch] font-display text-[clamp(2.3rem,4.8vw,4.4rem)] leading-[0.96] tracking-[-0.03em] text-white"
    >
      {heroHeadline}
    </m.h1>
  );
}

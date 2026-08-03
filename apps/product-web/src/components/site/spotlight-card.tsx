'use client';

import type { PropsWithChildren } from 'react';
import { useCallback, useRef } from 'react';
import { useReducedMotion } from 'framer-motion';

import { cn } from '@/lib/cn';

type SpotlightCardProps = PropsWithChildren<{
  className?: string;
}>;

export function SpotlightCard({ children, className }: SpotlightCardProps) {
  const reduceMotion = useReducedMotion();
  const cardRef = useRef<HTMLDivElement>(null);
  const spotlightRef = useRef<HTMLDivElement>(null);

  const handleMouseMove = useCallback(
    (event: React.MouseEvent<HTMLElement>) => {
      if (reduceMotion) return;
      const card = cardRef.current;
      const spotlight = spotlightRef.current;
      if (!card || !spotlight) return;

      const rect = card.getBoundingClientRect();
      const x = ((event.clientX - rect.left) / rect.width) * 100;
      const y = ((event.clientY - rect.top) / rect.height) * 100;

      // Use CSS custom properties directly instead of React state to avoid re-renders
      spotlight.style.background = `radial-gradient(420px circle at ${x}% ${y}%, rgba(96,165,250,0.18), transparent 42%)`;
      spotlight.style.opacity = '1';

      const rx = (0.5 - (event.clientY - rect.top) / rect.height) * 10;
      const ry = ((event.clientX - rect.left) / rect.width - 0.5) * 10;
      card.style.transform = `perspective(800px) rotateX(${rx}deg) rotateY(${ry}deg)`;
    },
    [reduceMotion],
  );

  const handleMouseLeave = useCallback(() => {
    const card = cardRef.current;
    const spotlight = spotlightRef.current;
    if (!card || !spotlight) return;

    spotlight.style.opacity = '0';
    card.style.transform = 'perspective(800px) rotateX(0deg) rotateY(0deg)';
  }, []);

  return (
    <article
      ref={cardRef}
      className={cn(
        'group relative min-w-0 overflow-hidden rounded-[30px] border border-white/10 bg-white/[0.05] p-5 backdrop-blur-2xl shadow-luxe transition duration-300 sm:p-6',
        className,
      )}
      onMouseMove={handleMouseMove}
      onMouseLeave={handleMouseLeave}
      style={{ transformStyle: 'preserve-3d', willChange: 'transform' }}
    >
      <div
        ref={spotlightRef}
        className="pointer-events-none absolute inset-0 opacity-0 transition duration-300"
      />
      <div className="pointer-events-none absolute inset-0 rounded-[30px] border border-white/10 [mask-image:linear-gradient(180deg,black,transparent)]" />
      <div className="relative z-10">{children}</div>
    </article>
  );
}
'use client';

import type { PropsWithChildren } from 'react';

import { cn } from '@/lib/cn';

/**
 * Calm surface card — flat, border-only, quiet hover. No 3D tilt, no
 * pointer-tracking spotlight glow, no backdrop blur (calm pass).
 */
export function SpotlightCard({ children, className }: PropsWithChildren<{ className?: string }>) {
  return (
    <article
      className={cn(
        'group relative min-w-0 overflow-hidden rounded-2xl border border-white/10 bg-white/[0.04] p-5 transition-colors duration-200 hover:border-white/20 sm:p-6',
        className,
      )}
    >
      <div className="relative z-10">{children}</div>
    </article>
  );
}

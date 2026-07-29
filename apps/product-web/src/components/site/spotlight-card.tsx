'use client';

import type { PropsWithChildren } from 'react';
import { useMemo, useState } from 'react';
import { motion, useReducedMotion } from 'framer-motion';

import { cn } from '@/lib/cn';

type SpotlightCardProps = PropsWithChildren<{
  className?: string;
}>;

export function SpotlightCard({ children, className }: SpotlightCardProps) {
  const reduceMotion = useReducedMotion();
  const [state, setState] = useState({ x: 50, y: 50, rx: 0, ry: 0 });

  const style = useMemo(
    () => ({
      background: `radial-gradient(420px circle at ${state.x}% ${state.y}%, rgba(96,165,250,0.18), transparent 42%)`,
    }),
    [state.x, state.y],
  );

  return (
    <motion.article
      className={cn(
        'group relative overflow-hidden rounded-[30px] border border-white/10 bg-white/[0.05] p-6 backdrop-blur-2xl shadow-luxe transition duration-300',
        className,
      )}
      animate={reduceMotion ? {} : { rotateX: state.rx, rotateY: state.ry }}
      transition={{ type: 'spring', stiffness: 180, damping: 20, mass: 0.5 }}
      onMouseMove={(event) => {
        if (reduceMotion) return;
        const rect = event.currentTarget.getBoundingClientRect();
        const x = ((event.clientX - rect.left) / rect.width) * 100;
        const y = ((event.clientY - rect.top) / rect.height) * 100;
        const rx = (0.5 - (event.clientY - rect.top) / rect.height) * 10;
        const ry = (((event.clientX - rect.left) / rect.width) - 0.5) * 10;
        setState({ x, y, rx, ry });
      }}
      onMouseLeave={() => setState({ x: 50, y: 50, rx: 0, ry: 0 })}
      style={{ transformStyle: 'preserve-3d' }}
    >
      <div className="pointer-events-none absolute inset-0 opacity-0 transition duration-300 group-hover:opacity-100" style={style} />
      <div className="pointer-events-none absolute inset-0 rounded-[30px] border border-white/10 [mask-image:linear-gradient(180deg,black,transparent)]" />
      <div className="relative z-10">{children}</div>
    </motion.article>
  );
}
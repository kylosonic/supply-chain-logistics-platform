'use client';

import type { PropsWithChildren } from 'react';
import { motion, useReducedMotion } from 'framer-motion';

import { cn } from '@/lib/cn';

type MotionSectionProps = PropsWithChildren<{
  className?: string;
  delay?: number;
}>;

export function MotionSection({ children, className, delay = 0 }: MotionSectionProps) {
  const reduceMotion = useReducedMotion();

  if (reduceMotion) {
    return <div className={className}>{children}</div>;
  }

  return (
    <motion.section
      className={cn(className)}
      initial={{ opacity: 0, y: 28, filter: 'blur(18px)' }}
      whileInView={{ opacity: 1, y: 0, filter: 'blur(0px)' }}
      viewport={{ once: true, margin: '-80px' }}
      transition={{ duration: 0.85, ease: [0.16, 1, 0.3, 1], delay }}
    >
      {children}
    </motion.section>
  );
}
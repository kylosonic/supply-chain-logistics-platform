'use client';

import type { PropsWithChildren } from 'react';
import { LazyMotion, domAnimation } from 'framer-motion';

export function MotionProvider({ children }: PropsWithChildren) {
  return (
    <LazyMotion features={domAnimation} strict={false}>
      {children}
    </LazyMotion>
  );
}

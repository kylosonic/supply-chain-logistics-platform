'use client';

import Link from 'next/link';
import type { PropsWithChildren } from 'react';
import { useMemo, useState } from 'react';
import { m, useReducedMotion } from 'framer-motion';
import { ArrowUpRight } from 'lucide-react';

import { cn } from '@/lib/cn';

type MagneticLinkProps = PropsWithChildren<{
  href: string;
  variant?: 'primary' | 'secondary' | 'ghost';
  className?: string;
  showIcon?: boolean;
  external?: boolean;
}>;

const variantClasses: Record<NonNullable<MagneticLinkProps['variant']>, string> = {
  primary:
    'bg-sky-500 text-slate-950 transition-colors hover:bg-sky-400',
  secondary:
    'border border-white/12 bg-white/[0.04] text-white transition-colors hover:bg-white/[0.08]',
  ghost: 'border border-white/10 bg-transparent text-white/78 hover:text-white',
};

function useMagnet() {
  const [offset, setOffset] = useState({ x: 0, y: 0 });
  const reduceMotion = useReducedMotion();

  const handlers = useMemo(
    () => ({
      onMouseMove: (event: React.MouseEvent<HTMLElement>) => {
        if (reduceMotion) return;
        const rect = event.currentTarget.getBoundingClientRect();
        const x = (event.clientX - rect.left - rect.width / 2) * 0.12;
        const y = (event.clientY - rect.top - rect.height / 2) * 0.12;
        setOffset({ x, y });
      },
      onMouseLeave: () => setOffset({ x: 0, y: 0 }),
    }),
    [reduceMotion],
  );

  return { offset, handlers };
}

function LinkContent({ children, showIcon = true }: Pick<MagneticLinkProps, 'showIcon'> & PropsWithChildren) {
  return (
    <span className="relative z-10 flex items-center justify-center gap-2 text-center sm:text-left">
      {children}
      {showIcon ? <ArrowUpRight className="h-4 w-4 transition group-hover:-translate-y-0.5 group-hover:translate-x-0.5" /> : null}
    </span>
  );
}

function AnchorShell({
  children,
  href,
  external,
  className,
  variant = 'primary',
  showIcon = true,
}: PropsWithChildren<MagneticLinkProps>) {
  const { offset, handlers } = useMagnet();
  const content = <LinkContent showIcon={showIcon}>{children}</LinkContent>;
  const sharedClassName = cn(
    'group inline-flex min-h-12 min-w-0 items-center justify-center overflow-hidden rounded-lg px-4 text-sm font-semibold transition will-change-transform sm:px-5',
    variantClasses[variant],
    className,
  );

  const motionProps = {
    ...handlers,
    animate: { x: offset.x, y: offset.y },
    transition: { type: 'spring' as const, stiffness: 260, damping: 18, mass: 0.35 },
    className: sharedClassName,
  };

  if (external) {
    return (
      <m.a href={href} target="_blank" rel="noopener noreferrer" {...motionProps}>
        {content}
      </m.a>
    );
  }

  return (
    <Link href={href} className="inline-flex">
      <m.span {...motionProps}>{content}</m.span>
    </Link>
  );
}

export function MagneticLink({ href, external, ...props }: MagneticLinkProps) {
  const isExternal = external ?? href.startsWith('http');

  return <AnchorShell href={href} external={isExternal} {...props} />;
}
'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import type { PropsWithChildren } from 'react';
import { useEffect, useMemo, useState } from 'react';
import { AnimatePresence, motion, useScroll } from 'framer-motion';
import { ArrowUpRight, Dot, Sparkles } from 'lucide-react';

import { cn } from '@/lib/cn';
import { externalLinks, navigation } from '@/lib/site-content';

import { MagneticLink } from './magnetic-link';

export function SiteChrome({ children }: PropsWithChildren) {
  const pathname = usePathname();
  const { scrollY } = useScroll();
  const [compact, setCompact] = useState(false);
  const [menuOpen, setMenuOpen] = useState(false);

  useEffect(() => {
    const unsubscribe = scrollY.on('change', (value) => setCompact(value > 24));
    return () => unsubscribe();
  }, [scrollY]);

  useEffect(() => {
    let frame = 0;
    const onMove = (event: MouseEvent) => {
      cancelAnimationFrame(frame);
      frame = requestAnimationFrame(() => {
        document.documentElement.style.setProperty('--spotlight-x', `${event.clientX}px`);
        document.documentElement.style.setProperty('--spotlight-y', `${event.clientY}px`);
      });
    };

    window.addEventListener('mousemove', onMove, { passive: true });
    return () => {
      cancelAnimationFrame(frame);
      window.removeEventListener('mousemove', onMove);
    };
  }, []);

  useEffect(() => setMenuOpen(false), [pathname]);

  const footerLinks = useMemo(() => navigation.filter((item) => item.href !== '/'), []);

  return (
    <div className="relative min-h-screen overflow-x-hidden">
      <div className="pointer-events-none fixed inset-0 z-0 bg-[radial-gradient(circle_at_var(--spotlight-x,50%)_var(--spotlight-y,20%),rgba(59,130,246,0.18),transparent_18%),radial-gradient(circle_at_85%_14%,rgba(167,139,250,0.18),transparent_20%)]" />
      <div className="pointer-events-none fixed inset-0 z-0 opacity-40 [background-image:linear-gradient(rgba(255,255,255,0.06)_1px,transparent_1px),linear-gradient(90deg,rgba(255,255,255,0.06)_1px,transparent_1px)] [background-size:36px_36px]" />
      <div className="pointer-events-none fixed inset-0 z-0 bg-[radial-gradient(circle_at_top_left,rgba(34,211,238,0.09),transparent_25%),radial-gradient(circle_at_bottom_right,rgba(192,132,252,0.1),transparent_24%)]" />

      <header className="sticky top-0 z-40 px-3 pt-3 sm:px-6 sm:pt-4 lg:px-8">
        <motion.div
          className={cn(
            'mx-auto flex w-full max-w-[1380px] items-center justify-between gap-3 rounded-full border border-white/10 bg-black/35 px-4 py-3 backdrop-blur-2xl shadow-[0_24px_80px_rgba(0,0,0,0.32)] sm:gap-4',
            compact ? 'max-w-[1320px] px-4 py-2.5' : 'sm:px-5 sm:py-3.5',
          )}
          animate={{ scale: compact ? 0.985 : 1 }}
          transition={{ duration: 0.3, ease: [0.16, 1, 0.3, 1] }}
        >
          <Link href="/" className="inline-flex items-center gap-3 no-underline">
            <span className="inline-grid h-10 w-10 place-items-center rounded-[16px] border border-white/15 bg-white/[0.08] font-display text-sm font-semibold text-white shadow-[0_12px_40px_rgba(96,165,250,0.15)]">
              FP
            </span>
            <span className="hidden sm:grid">
              <strong className="font-display text-sm text-white">FreightPilot</strong>
              <span className="text-xs text-white/48">AI logistics control layer</span>
            </span>
          </Link>

          <nav className="hidden items-center gap-2 lg:flex">
            {navigation.map((item) => {
              const active = pathname === item.href;
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={cn(
                    'relative inline-flex items-center gap-2 rounded-full px-4 py-2 text-sm text-white/68 transition hover:text-white',
                    active && 'bg-white/[0.06] text-white shadow-[0_0_0_1px_rgba(255,255,255,0.08)]',
                  )}
                >
                  {active ? <Sparkles className="h-4 w-4 text-cyan-200" /> : <Dot className="h-4 w-4" />}
                  {item.label}
                </Link>
              );
            })}
          </nav>

          <div className="hidden items-center gap-3 lg:flex">
            <MagneticLink href={externalLinks.docs} variant="ghost" external>
              Docs
            </MagneticLink>
            <MagneticLink href="/launch" variant="primary">
              Launch FreightPilot
            </MagneticLink>
          </div>

          <button
            type="button"
            onClick={() => setMenuOpen((open) => !open)}
            className="inline-flex items-center gap-3 rounded-full border border-white/10 bg-white/[0.04] px-4 py-2.5 text-sm text-white/78 lg:hidden"
            aria-expanded={menuOpen}
            aria-label="Toggle navigation"
          >
            <span className="font-medium">Menu</span>
            <span className="relative inline-flex h-6 w-10 items-center justify-center">
              {[0, 1, 2].map((index) => (
                <motion.span
                  key={index}
                  className="absolute h-1.5 w-1.5 rounded-full bg-cyan-200"
                  animate={
                    menuOpen
                      ? {
                          x: index === 1 ? 0 : index === 0 ? -8 : 8,
                          y: 0,
                          opacity: 1,
                        }
                      : {
                          x: index === 1 ? 0 : index === 0 ? -8 : 8,
                          y: index === 1 ? 0 : index === 0 ? -6 : 6,
                          opacity: 1,
                        }
                  }
                  transition={{ duration: 0.28, ease: [0.16, 1, 0.3, 1] }}
                />
              ))}
            </span>
          </button>
        </motion.div>
      </header>

      <AnimatePresence>
        {menuOpen ? (
          <motion.div
            initial={{ opacity: 0, y: -18 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -18 }}
            transition={{ duration: 0.28, ease: [0.16, 1, 0.3, 1] }}
            className="fixed inset-x-3 top-20 z-30 rounded-[28px] border border-white/10 bg-black/78 p-5 backdrop-blur-2xl shadow-[0_24px_80px_rgba(0,0,0,0.38)] sm:inset-x-6 sm:top-24 lg:hidden"
          >
            <div className="grid gap-3">
              {navigation.map((item) => (
                <Link
                  key={item.href}
                  href={item.href}
                  className={cn(
                    'rounded-[20px] border border-white/10 bg-white/[0.04] px-4 py-4 text-white/75 transition hover:text-white',
                    pathname === item.href && 'border-cyan-400/30 bg-cyan-400/10 text-white',
                  )}
                >
                  <span className="block font-display text-lg text-white">{item.label}</span>
                  <span className="mt-1 block text-sm text-white/48">{item.description}</span>
                </Link>
              ))}
            </div>
            <div className="mt-5 grid gap-3 sm:grid-cols-2">
              <MagneticLink href={externalLinks.docs} variant="secondary" external>
                Open docs
              </MagneticLink>
              <MagneticLink href={externalLinks.console} variant="primary" external>
                Open console
              </MagneticLink>
            </div>
          </motion.div>
        ) : null}
      </AnimatePresence>

      <main className="relative z-10 pb-20 pt-4 sm:pb-24 sm:pt-6 lg:pt-8">{children}</main>

      <footer className="relative z-10 border-t border-white/10 px-3 pb-10 pt-6 sm:px-6 sm:pt-8 lg:px-8">
        <div className="section-shell flex flex-col gap-8 rounded-[32px] border border-white/10 bg-white/[0.04] px-5 py-6 backdrop-blur-xl sm:px-6 lg:flex-row lg:items-end lg:justify-between lg:px-8 lg:py-7">
          <div className="max-w-xl space-y-3">
            <p className="kicker">FreightPilot</p>
            <h3 className="font-display text-2xl text-white">The future-facing logistics command layer.</h3>
            <p className="text-sm leading-7 text-white/56">
              Built to feel premium, deliberate, and operationally intelligent from first scroll to first launch.
            </p>
          </div>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {footerLinks.map((item) => (
              <Link key={item.href} href={item.href} className="rounded-[20px] border border-white/10 bg-black/20 px-4 py-4 text-sm text-white/70 no-underline transition hover:border-white/20 hover:text-white">
                <span className="block font-medium text-white">{item.label}</span>
                <span className="mt-1 block text-white/44">{item.description}</span>
              </Link>
            ))}
          </div>
          <MagneticLink href={externalLinks.desktop} variant="secondary" external>
            Download desktop
          </MagneticLink>
        </div>
      </footer>
    </div>
  );
}
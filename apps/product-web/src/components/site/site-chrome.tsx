'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import type { PropsWithChildren } from 'react';
import { useEffect, useMemo, useState } from 'react';
import { AnimatePresence, m, useScroll } from 'framer-motion';
import { ArrowUp, ArrowUpRight, Dot, Sparkles } from 'lucide-react';

import { cn } from '@/lib/cn';
import { externalLinks, footerNavigation, navigation } from '@/lib/site-content';

import { MagneticLink } from './magnetic-link';

export function SiteChrome({ children }: PropsWithChildren) {
  const pathname = usePathname();
  const { scrollY } = useScroll();
  const [compact, setCompact] = useState(false);
  const [menuOpen, setMenuOpen] = useState(false);
  const [showBackToTop, setShowBackToTop] = useState(false);

  useEffect(() => {
    const unsubscribe = scrollY.on('change', (value) => {
      setCompact(value > 24);
      setShowBackToTop(value > 600);
    });
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

  // Close mobile menu on Escape key
  useEffect(() => {
    if (!menuOpen) return;
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') setMenuOpen(false);
    };
    window.addEventListener('keydown', onKeyDown);
    return () => window.removeEventListener('keydown', onKeyDown);
  }, [menuOpen]);

  // Lock body scroll when mobile menu is open
  useEffect(() => {
    if (menuOpen) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = '';
    }
    return () => {
      document.body.style.overflow = '';
    };
  }, [menuOpen]);

  const currentYear = new Date().getFullYear();

  return (
    <div className="relative min-h-screen overflow-x-hidden">
      {/* Consolidated into a single performant background layer instead of 3 separate divs */}
      <div className="pointer-events-none fixed inset-0 z-0 bg-[radial-gradient(circle_at_var(--spotlight-x,50%)_var(--spotlight-y,20%),rgba(59,130,246,0.18),transparent_18%),radial-gradient(circle_at_85%_14%,rgba(167,139,250,0.14),transparent_20%),radial-gradient(circle_at_top_left,rgba(34,211,238,0.06),transparent_25%),radial-gradient(circle_at_bottom_right,rgba(192,132,252,0.06),transparent_24%)]" />
      <div className="pointer-events-none fixed inset-0 z-0 opacity-15 sm:opacity-20 [background-image:linear-gradient(rgba(255,255,255,0.05)_1px,transparent_1px),linear-gradient(90deg,rgba(255,255,255,0.05)_1px,transparent_1px)] [background-size:40px_40px]" />

      <header className="sticky top-0 z-40 px-3 pt-2.5 sm:px-6 sm:pt-4 lg:px-8">
        <m.div
          className={cn(
            'mx-auto flex w-full max-w-[1380px] items-center justify-between gap-3 rounded-[28px] border border-white/10 bg-black/35 px-4 py-2.5 backdrop-blur-2xl shadow-[0_24px_80px_rgba(0,0,0,0.32)] sm:gap-4 sm:rounded-full sm:py-3',
            compact ? 'max-w-[1320px] px-4 py-2' : 'sm:px-5 sm:py-3',
          )}
          animate={{ scale: compact ? 0.985 : 1 }}
          transition={{ duration: 0.3, ease: [0.16, 1, 0.3, 1] }}
        >
          <Link href="/" className="inline-flex items-center gap-3 no-underline">
            <span className="inline-grid h-8 w-8 place-items-center rounded-[14px] border border-white/15 bg-white/[0.08] font-display text-sm font-semibold text-white shadow-[0_12px_40px_rgba(96,165,250,0.15)] sm:h-10 sm:w-10 sm:rounded-[16px]">
              FP
            </span>
            <span className="hidden sm:grid">
              <strong className="font-display text-sm text-white">FreightPilot</strong>
              <span className="text-xs text-white/50">Logistics operations workspace</span>
            </span>
          </Link>

          <nav className="hidden items-center gap-2 lg:flex" aria-label="Main navigation">
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
                  aria-current={active ? 'page' : undefined}
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
            className="inline-flex items-center gap-3 rounded-full border border-white/10 bg-white/[0.04] px-3.5 py-2 text-sm text-white/78 sm:px-4 sm:py-2.5 lg:hidden"
            aria-expanded={menuOpen}
            aria-label="Toggle navigation"
          >
            <span className="font-medium">Menu</span>
            <span className="relative inline-flex h-6 w-10 items-center justify-center" aria-hidden="true">
              {[0, 1, 2].map((index) => (
                <m.span
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
        </m.div>
      </header>

      <AnimatePresence>
        {menuOpen ? (
          <>
            {/* Backdrop overlay for mobile menu */}
            <m.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.2 }}
              className="fixed inset-0 z-20 bg-black/50 backdrop-blur-sm lg:hidden"
              onClick={() => setMenuOpen(false)}
              aria-hidden="true"
            />
            <m.div
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
                    <span className="mt-1 block text-sm text-white/50">{item.description}</span>
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
            </m.div>
          </>
        ) : null}
      </AnimatePresence>

      <main id="main-content" className="relative z-10 pb-20 pt-4 sm:pb-24 sm:pt-6 lg:pt-8">{children}</main>

      <footer className="relative z-10 mt-12 border-t border-white/10 px-3 pb-10 pt-10 sm:px-6 sm:pt-16 lg:px-8">
        <div className="section-shell grid gap-12 lg:grid-cols-[1.5fr_2fr] lg:gap-8">
          <div className="max-w-md space-y-6">
            <Link href="/" className="inline-flex items-center gap-3 no-underline">
              <span className="inline-grid h-8 w-8 place-items-center rounded-[14px] border border-white/15 bg-white/[0.08] font-display text-sm font-semibold text-white shadow-[0_12px_40px_rgba(96,165,250,0.15)] sm:h-10 sm:w-10 sm:rounded-[16px]">
                FP
              </span>
              <span className="grid">
                <strong className="font-display text-sm text-white">FreightPilot</strong>
                <span className="text-xs text-white/50">Logistics operations workspace</span>
              </span>
            </Link>
            <p className="text-sm leading-7 text-white/60">
              Built to give operators one place to plan routes, handle exceptions, manage provider controls, and launch new workspaces securely and reliably.
            </p>
            <div className="flex gap-4 pt-2">
              <MagneticLink href="/contact" variant="primary">
                Contact Sales
              </MagneticLink>
            </div>
          </div>
          
          <div className="grid grid-cols-2 gap-8 sm:grid-cols-4">
            <div className="space-y-4">
              <h4 className="font-display text-sm text-white">Platform</h4>
              <ul className="space-y-3">
                {footerNavigation.platform.map((item) => (
                  <li key={item.label}>
                    <Link href={item.href} className="text-sm text-white/60 transition hover:text-white">
                      {item.label}
                    </Link>
                  </li>
                ))}
              </ul>
            </div>
            <div className="space-y-4">
              <h4 className="font-display text-sm text-white">Resources</h4>
              <ul className="space-y-3">
                {footerNavigation.resources.map((item) => (
                  <li key={item.label}>
                    <Link href={item.href} className="text-sm text-white/60 transition hover:text-white" {...(item.href.startsWith('http') ? { target: '_blank', rel: 'noopener noreferrer' } : {})}>
                      {item.label}
                    </Link>
                  </li>
                ))}
              </ul>
            </div>
            <div className="space-y-4">
              <h4 className="font-display text-sm text-white">Company</h4>
              <ul className="space-y-3">
                {footerNavigation.company.map((item) => (
                  <li key={item.label}>
                    <Link href={item.href} className="text-sm text-white/60 transition hover:text-white">
                      {item.label}
                    </Link>
                  </li>
                ))}
              </ul>
            </div>
            <div className="space-y-4">
              <h4 className="font-display text-sm text-white">Legal</h4>
              <ul className="space-y-3">
                {footerNavigation.legal.map((item) => (
                  <li key={item.label}>
                    <Link href={item.href} className="text-sm text-white/60 transition hover:text-white">
                      {item.label}
                    </Link>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </div>

        {/* Legal footer row */}
        <div className="section-shell mt-12 flex flex-col items-center justify-between gap-4 border-t border-white/10 pt-8 text-xs text-white/40 sm:flex-row">
          <p>© {currentYear} FreightPilot. All rights reserved.</p>
          <div className="flex items-center gap-6">
            <span className="flex items-center gap-2">
              <span className="h-1.5 w-1.5 rounded-full bg-emerald-400"></span>
              All systems operational
            </span>
          </div>
        </div>
      </footer>

      {/* Back-to-top button */}
      <AnimatePresence>
        {showBackToTop ? (
          <m.button
            initial={{ opacity: 0, scale: 0.8 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.8 }}
            transition={{ duration: 0.25 }}
            type="button"
            className="back-to-top"
            onClick={() => window.scrollTo({ top: 0, behavior: 'smooth' })}
            aria-label="Back to top"
          >
            <ArrowUp className="h-4 w-4" />
          </m.button>
        ) : null}
      </AnimatePresence>
    </div>
  );
}
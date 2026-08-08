import { useEffect, useRef } from 'react';
import { useLocation, useNavigationType } from 'react-router-dom';

import { createScrollPositions } from '../services/scrollPositions';
import type { ScrollPositions } from '../services/scrollPositions';

/**
 * NB-58: window scroll save/restore (TECH-75).
 *
 * Renders null. The store is a pure in-memory Map factory created exactly
 * once per app lifetime (lazy ref init). The WINDOW scrolls — the desktop
 * sidebar scrolls internally and is preserved automatically because the
 * shell stays mounted (Phase 2).
 *
 * - Save: passive window scroll listener, debounced ~100ms, keyed by the
 *   current pathname.
 * - Restore: POP (back/forward) → saved position ?? top; PUSH/REPLACE →
 *   top (including the catch-all `<Navigate to="/" replace />`).
 *
 * Positions are in-memory only: hard reloads fall back to the browser's
 * native `history.scrollRestoration` (left untouched). `typeof window`
 * guards keep SSR safe (effects never run under renderToString).
 */
export function ScrollManager() {
  const { pathname } = useLocation();
  const navigationType = useNavigationType();

  const storeRef = useRef<ScrollPositions | null>(null);
  if (storeRef.current === null) {
    storeRef.current = createScrollPositions();
  }
  const store = storeRef.current;

  // The save listener stays attached for the app lifetime (mount-only) but
  // must always write under the CURRENT pathname.
  const latestPathnameRef = useRef(pathname);
  useEffect(() => {
    latestPathnameRef.current = pathname;
  }, [pathname]);

  useEffect(() => {
    if (typeof window === 'undefined') return;
    let timer: ReturnType<typeof setTimeout> | undefined;
    const onScroll = () => {
      if (timer !== undefined) clearTimeout(timer);
      timer = setTimeout(() => {
        store.save(latestPathnameRef.current, window.scrollY);
      }, 100);
    };
    window.addEventListener('scroll', onScroll, { passive: true });
    return () => {
      if (timer !== undefined) clearTimeout(timer);
      window.removeEventListener('scroll', onScroll);
    };
  }, [store]);

  useEffect(() => {
    if (typeof window === 'undefined') return;
    if (navigationType === 'POP') {
      const saved = store.get(pathname);
      window.scrollTo(0, saved ?? 0);
    } else {
      window.scrollTo(0, 0);
    }
  }, [pathname, navigationType, store]);

  return null;
}

import { useEffect, useRef } from 'react';
import type { ReactNode } from 'react';
import { useLocation } from 'react-router-dom';

/**
 * NB-57: one subtle ~140ms content fade per page switch (TECH-74).
 *
 * Renders a plain div keyed by `location.pathname`; the key change remounts
 * only the wrapper + outlet content and re-triggers the `.fp-page-fade` CSS
 * animation. The shell never remounts — Layout itself is never keyed.
 *
 * First-login-load suppression: the very first layout mount (login →
 * dashboard landing) is an auth-flow completion, not a page switch, so the
 * wrapper renders WITHOUT the class. The `suppressMountRef` flag starts
 * `true` and flips to `false` in a mount-only effect (never written during
 * render — StrictMode-safe), so every subsequent pathname change mounts the
 * new keyed div WITH the class, while same-pathname renders reuse the
 * mounted div (no replay).
 */
export function PageTransition({ children }: { children: ReactNode }) {
  const { pathname } = useLocation();
  const suppressMountRef = useRef(true);

  useEffect(() => {
    suppressMountRef.current = false;
  }, []);

  const animate = !suppressMountRef.current;

  return (
    <div key={pathname} className={animate ? 'fp-page-fade' : undefined}>
      {children}
    </div>
  );
}

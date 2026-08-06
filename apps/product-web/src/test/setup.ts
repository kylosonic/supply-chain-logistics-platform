/**
 * Global test shims (vitest `setupFiles`).
 *
 * Runs in BOTH environments (node default + jsdom pragma files). Framer-motion
 * hooks (`useReducedMotion`, `useInView`) and RTL interactions require
 * `window.matchMedia` and `ResizeObserver` in jsdom; guard so the node
 * environment is untouched.
 */

type MediaQueryListShim = {
  matches: boolean;
  media: string;
  onchange: null;
  addListener: () => void;
  removeListener: () => void;
  addEventListener: () => void;
  removeEventListener: () => void;
  dispatchEvent: () => boolean;
};

if (typeof window !== 'undefined') {
  if (!window.matchMedia) {
    window.matchMedia = (query: string): MediaQueryList => {
      const shim: MediaQueryListShim = {
        matches: false,
        media: query,
        onchange: null,
        addListener: () => undefined,
        removeListener: () => undefined,
        addEventListener: () => undefined,
        removeEventListener: () => undefined,
        dispatchEvent: () => false,
      };
      return shim as unknown as MediaQueryList;
    };
  }

  if (!('ResizeObserver' in window)) {
    class ResizeObserverShim {
      observe(): void {}
      unobserve(): void {}
      disconnect(): void {}
    }

    (window as Window & { ResizeObserver: unknown }).ResizeObserver = ResizeObserverShim;
  }
}

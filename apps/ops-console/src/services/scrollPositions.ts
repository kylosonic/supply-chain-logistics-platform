/**
 * In-memory window-scroll position store (TECH-75 / NB-58).
 *
 * Plain `Map` behind a pure factory — no module-level mutable state, so every
 * consumer (app shell, tests, SSR) gets its own isolated instance. Positions
 * are keyed by pathname only: no console page varies scroll by search params.
 * Positions are intentionally NOT persisted: hard reloads are handled by the
 * browser's native `history.scrollRestoration`.
 */
export interface ScrollPositions {
  save(path: string, y: number): void;
  get(path: string): number | undefined;
  clear(): void;
}

export function createScrollPositions(): ScrollPositions {
  const positions = new Map<string, number>();

  return {
    save(path, y) {
      positions.set(path, y);
    },
    get(path) {
      return positions.get(path);
    },
    clear() {
      positions.clear();
    },
  };
}

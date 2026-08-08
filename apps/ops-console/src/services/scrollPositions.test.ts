import { describe, expect, it } from 'vitest';

import { createScrollPositions } from './scrollPositions';

describe('createScrollPositions (TECH-75 / NB-58)', () => {
  it('saves and restores a scroll position per path (NB-58.1 roundtrip)', () => {
    const store = createScrollPositions();
    store.save('/alerts', 640);
    expect(store.get('/alerts')).toBe(640);
    store.save('/alerts', 120);
    expect(store.get('/alerts')).toBe(120);
  });

  it('returns undefined for an unknown path (POP restore falls back to top)', () => {
    const store = createScrollPositions();
    expect(store.get('/shipments')).toBeUndefined();
  });

  it('clear() empties every saved position', () => {
    const store = createScrollPositions();
    store.save('/alerts', 640);
    store.save('/dashboard', 300);
    store.clear();
    expect(store.get('/alerts')).toBeUndefined();
    expect(store.get('/dashboard')).toBeUndefined();
  });

  it('keeps factory instances independent (no module-level mutable state)', () => {
    const a = createScrollPositions();
    const b = createScrollPositions();
    a.save('/alerts', 640);
    expect(a.get('/alerts')).toBe(640);
    expect(b.get('/alerts')).toBeUndefined();
  });
});

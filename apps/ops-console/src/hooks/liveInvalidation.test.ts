import { afterEach, describe, expect, it, vi } from 'vitest';

import {
  LIVE_INVALIDATION_WINDOW_MS,
  LIVE_PAYLOAD_QUERY_KEYS,
  createCoalescedInvalidator,
  livePayloadQueryKeys,
} from './liveInvalidation';
import type { LiveUpdatePayload } from './useLiveUpdates';

function fullPayload(overrides: Partial<LiveUpdatePayload> = {}): LiveUpdatePayload {
  return {
    type: 'live_update',
    server_time: '2026-08-08T12:00:00Z',
    inventory_overview: [],
    route_summaries: [],
    forecast_preview: [],
    dispatch_overview: { updated_at: null, runs: [] },
    ...overrides,
  };
}

afterEach(() => {
  vi.useRealTimers();
});

describe('live payload invalidation mapping (TECH-73 decision 5)', () => {
  it('exposes the 15s coalescing window constant', () => {
    expect(LIVE_INVALIDATION_WINDOW_MS).toBe(15_000);
  });

  it('maps the three live payload fields to their payload-scoped query-key prefixes', () => {
    expect(LIVE_PAYLOAD_QUERY_KEYS).toEqual({
      inventory_overview: ['inventory'],
      route_summaries: ['routes'],
      forecast_preview: ['forecast'],
      dispatch_overview: ['dispatch'],
    });
  });

  it('maps a full payload to exactly inventory/routes/forecast/dispatch — never shipments/subscriptions/activation', () => {
    const keys = livePayloadQueryKeys(fullPayload());
    expect(keys).toEqual([['inventory'], ['routes'], ['forecast'], ['dispatch']]);
    expect(keys).not.toContain(['shipments']);
    expect(keys).not.toContain(['subscriptions']);
    expect(keys).not.toContain(['activation']);
  });

  it('skips absent payload fields', () => {
    expect(livePayloadQueryKeys({ inventory_overview: [] })).toEqual([['inventory']]);
    expect(livePayloadQueryKeys({ route_summaries: [] })).toEqual([['routes']]);
    expect(livePayloadQueryKeys({ dispatch_overview: { updated_at: null, runs: [] } })).toEqual([
      ['dispatch'],
    ]);
    expect(livePayloadQueryKeys({})).toEqual([]);
  });
});

describe('createCoalescedInvalidator (TECH-73 decision 6)', () => {
  it('flushes at most once per window, carrying the LATEST payload seen (t0/t5/t9 → t15, then t16 → t31)', () => {
    vi.useFakeTimers();
    const flush = vi.fn();
    const coalescer = createCoalescedInvalidator(15_000, flush);

    const p0 = fullPayload({ server_time: 't0' });
    const p1 = fullPayload({ server_time: 't5' });
    const p2 = fullPayload({ server_time: 't9' });
    const p3 = fullPayload({ server_time: 't16' });

    coalescer.push(p0);
    vi.advanceTimersByTime(5_000);
    coalescer.push(p1);
    vi.advanceTimersByTime(4_000);
    coalescer.push(p2);
    vi.advanceTimersByTime(6_000); // t15 — flush #1

    expect(flush).toHaveBeenCalledTimes(1);
    expect(flush).toHaveBeenCalledWith(p2); // latest payload in the window wins

    coalescer.push(p3); // t16 — a fresh window starts
    vi.advanceTimersByTime(15_000); // t31 — flush #2

    expect(flush).toHaveBeenCalledTimes(2);
    expect(flush).toHaveBeenLastCalledWith(p3);
  });

  it('uses the default 15s window when none is supplied', () => {
    vi.useFakeTimers();
    const flush = vi.fn();
    const coalescer = createCoalescedInvalidator(undefined as unknown as number, flush);

    coalescer.push(fullPayload());
    vi.advanceTimersByTime(15_000);
    expect(flush).toHaveBeenCalledTimes(1);
  });

  it('dispose() before the window elapses cancels the pending flush', () => {
    vi.useFakeTimers();
    const flush = vi.fn();
    const coalescer = createCoalescedInvalidator(15_000, flush);

    coalescer.push(fullPayload());
    coalescer.dispose();
    vi.advanceTimersByTime(20_000);

    expect(flush).not.toHaveBeenCalled();
  });

  it('never flushes when nothing was published', () => {
    vi.useFakeTimers();
    const flush = vi.fn();
    const coalescer = createCoalescedInvalidator(15_000, flush);

    vi.advanceTimersByTime(30_000);
    coalescer.dispose();

    expect(flush).not.toHaveBeenCalled();
  });
});

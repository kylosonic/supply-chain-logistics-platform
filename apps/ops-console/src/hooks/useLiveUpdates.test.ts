import { createElement } from 'react';
import { renderToString } from 'react-dom/server';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import {
  getLivePayload,
  publishLivePayload,
  resetLivePayloadStore,
  subscribeLivePayload,
  useLivePayload,
} from './useLiveUpdates';
import type { LiveUpdatePayload } from './useLiveUpdates';

function fullPayload(overrides: Partial<LiveUpdatePayload> = {}): LiveUpdatePayload {
  return {
    type: 'live_update',
    server_time: '2026-08-08T12:00:00Z',
    inventory_overview: [],
    route_summaries: [],
    forecast_preview: [],
    ...overrides,
  };
}

beforeEach(() => {
  resetLivePayloadStore();
});

afterEach(() => {
  resetLivePayloadStore();
});

describe('live payload module store (TECH-73 decision 4)', () => {
  it('publishLivePayload updates the getLivePayload snapshot', () => {
    expect(getLivePayload()).toBeNull();
    const payload = fullPayload({ server_time: '2026-08-08T09:30:00Z' });
    publishLivePayload(payload);
    expect(getLivePayload()).toBe(payload);
  });

  it('subscribing never fires the listener — only a NEW publish does (no replay on mount)', () => {
    const firstCalls = vi.fn();
    const secondCalls = vi.fn();
    const unsubscribe = subscribeLivePayload(firstCalls);
    expect(firstCalls).not.toHaveBeenCalled(); // never at subscribe time

    publishLivePayload(fullPayload());
    expect(firstCalls).toHaveBeenCalledTimes(1);

    // A second subscribe with no publish in between must not fire either.
    const unsubSecond = subscribeLivePayload(secondCalls);
    expect(firstCalls).toHaveBeenCalledTimes(1);
    expect(secondCalls).not.toHaveBeenCalled();

    publishLivePayload(fullPayload({ server_time: 'later' }));
    expect(firstCalls).toHaveBeenCalledTimes(2);
    expect(secondCalls).toHaveBeenCalledTimes(1);

    unsubscribe();
    unsubSecond();
  });

  it('supports multiple listeners with per-listener unsubscribe', () => {
    const firstCalls = vi.fn();
    const secondCalls = vi.fn();

    const unsubFirst = subscribeLivePayload(firstCalls);
    const unsubSecond = subscribeLivePayload(secondCalls);

    publishLivePayload(fullPayload({ server_time: 'a' }));
    expect(firstCalls).toHaveBeenCalledTimes(1);
    expect(secondCalls).toHaveBeenCalledTimes(1);

    unsubFirst();
    publishLivePayload(fullPayload({ server_time: 'b' }));
    expect(firstCalls).toHaveBeenCalledTimes(1);
    expect(secondCalls).toHaveBeenCalledTimes(2);

    unsubSecond();
    publishLivePayload(fullPayload({ server_time: 'c' }));
    expect(secondCalls).toHaveBeenCalledTimes(2);
  });

  it('resetLivePayloadStore clears the payload and all listeners', () => {
    const calls = vi.fn();
    subscribeLivePayload(calls);
    publishLivePayload(fullPayload());
    expect(calls).toHaveBeenCalledTimes(1);

    resetLivePayloadStore();
    expect(getLivePayload()).toBeNull();

    publishLivePayload(fullPayload());
    expect(calls).toHaveBeenCalledTimes(1); // listener was dropped with the reset
    expect(getLivePayload()).not.toBeNull();
  });
});

describe('useLivePayload SSR safety (TECH-73 decision 4)', () => {
  function ChipProbe() {
    const payload = useLivePayload();
    return createElement('span', null, payload ? payload.server_time : 'EMPTY');
  }

  it('renders nothing when the store is empty (getServerSnapshot path)', () => {
    const html = renderToString(createElement(ChipProbe));
    expect(html).toContain('EMPTY');
    expect(html).not.toContain('2026-08-08');
  });

  it('renders the seeded server_time when pre-published', () => {
    publishLivePayload(fullPayload({ server_time: '2026-08-08T12:34:56Z' }));
    const html = renderToString(createElement(ChipProbe));
    expect(html).toContain('2026-08-08T12:34:56Z');
  });
});

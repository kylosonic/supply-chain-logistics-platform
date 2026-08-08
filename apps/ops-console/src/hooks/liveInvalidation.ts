import type { LiveUpdatePayload } from './useLiveUpdates';

// ---------------------------------------------------------------------------
// TECH-73 (NB-56): payload-scoped, trailing-edge-coalesced live invalidation.
// Pure, React-free module — unit-testable in the node env (blueprint §3.5/.6).
// ---------------------------------------------------------------------------

/** At most one invalidation per window; the latest payload wins (no starvation). */
export const LIVE_INVALIDATION_WINDOW_MS = 15_000;

/** Live payload field → react-query key prefix (blueprint decision 5). */
export const LIVE_PAYLOAD_QUERY_KEYS: Record<
  'inventory_overview' | 'route_summaries' | 'forecast_preview',
  string[]
> = {
  inventory_overview: ['inventory'],
  route_summaries: ['routes'],
  forecast_preview: ['forecast'],
};

type LivePayloadFields = Pick<
  LiveUpdatePayload,
  'inventory_overview' | 'route_summaries' | 'forecast_preview'
>;

/** Maps the fields actually present in a payload to query-key prefixes.
 *  Absent fields are skipped; shipments/subscriptions/activation are never
 *  invalidated from live data (the payload never carries them). */
export function livePayloadQueryKeys(payload: Partial<LivePayloadFields>): string[][] {
  const keys: string[][] = [];
  for (const field of Object.keys(LIVE_PAYLOAD_QUERY_KEYS) as (keyof LivePayloadFields)[]) {
    if (payload[field] != null) {
      keys.push(LIVE_PAYLOAD_QUERY_KEYS[field]);
    }
  }
  return keys;
}

export type CoalescedInvalidator = {
  /** Records a payload; the first call in a window starts the timer. */
  push: (payload: LiveUpdatePayload) => void;
  /** Cancels any pending flush. */
  dispose: () => void;
};

/** Trailing-edge coalescer: the first push in a window starts the timer; later
 *  pushes only replace the held latest payload; exactly `windowMs` after the
 *  first push, invalidateFn runs with the LATEST payload. */
export function createCoalescedInvalidator(
  windowMs: number = LIVE_INVALIDATION_WINDOW_MS,
  invalidateFn: (payload: LiveUpdatePayload) => void,
): CoalescedInvalidator {
  let timer: ReturnType<typeof setTimeout> | null = null;
  let latest: LiveUpdatePayload | null = null;

  function flush() {
    timer = null;
    const payload = latest;
    latest = null;
    if (payload) invalidateFn(payload);
  }

  return {
    push(payload: LiveUpdatePayload) {
      latest = payload;
      if (timer === null) {
        timer = setTimeout(flush, windowMs);
      }
    },
    dispose() {
      if (timer !== null) {
        clearTimeout(timer);
        timer = null;
      }
      latest = null;
    },
  };
}

import { useEffect, useRef, useSyncExternalStore } from 'react';

import type {
  DispatchLiveOverview,
  ForecastPoint,
  InventoryOverviewRow,
  RouteScheduleSummary,
} from '../types/api';

export type LiveUpdatePayload = {
  type: 'live_update';
  server_time: string;
  inventory_overview: InventoryOverviewRow[];
  route_summaries: RouteScheduleSummary[];
  forecast_preview: ForecastPoint[];
  dispatch_overview?: DispatchLiveOverview;
};

type Props = {
  getToken: () => Promise<string | null>;
  enabled: boolean;
  onMessage: (payload: LiveUpdatePayload) => void;
};

let _wsToken: string | null = null;

export function clearLiveSession(): void {
  _wsToken = null;
  livePayload = null;
  for (const listener of livePayloadListeners) {
    listener();
  }
}

export function useLiveUpdates({ getToken, enabled, onMessage }: Props) {  const socketRef = useRef<WebSocket | null>(null);
  const onMessageRef = useRef(onMessage);
  onMessageRef.current = onMessage;

  useEffect(() => {
    if (!enabled) return;

    let cancelled = false;

    async function connect() {
      const token = _wsToken || await getToken();
      if (!token || cancelled) return;
      _wsToken = token;

      const apiBase = import.meta.env.VITE_API_BASE_URL || '/api/v1';
      const wsUrl = (() => {
        if (apiBase.startsWith('http://') || apiBase.startsWith('https://')) {
          const url = new URL(apiBase);
          const protocol = url.protocol === 'https:' ? 'wss:' : 'ws:';
          return `${protocol}//${url.host}${url.pathname}/live/updates`;
        }
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const basePath = apiBase.startsWith('/') ? apiBase : `/${apiBase}`;
        return `${protocol}//${window.location.host}${basePath}/live/updates`;
      })();

      const socket = new WebSocket(wsUrl, []);
      socketRef.current = socket;

      socket.onopen = () => {
        socket.send(JSON.stringify({ type: 'auth', token }));
      };

      socket.onmessage = (event) => {
        try {
          const parsed = JSON.parse(event.data) as LiveUpdatePayload;
          if (parsed.type === 'live_update') {
            onMessageRef.current(parsed);
          }
        } catch {
          // ignore malformed payloads
        }
      };
    }

    connect();

    return () => {
      cancelled = true;
      socketRef.current?.close();
    };
  }, [enabled, getToken]);
}

// module-level live payload store (session-scoped). The single
// socket owner (SessionLiveUpdates, mounted once in Layout) publishes here;
// the dashboard chip + coalesced invalidation and the Route Studio schedule
// stream consume it. Same pub/sub pattern as the api.ts session signal; no
// context, no new dependency (useSyncExternalStore is core React 18).
// The socket itself cannot run in renderToString, so this store is the
// testable seam (blueprint decision 4).

let livePayload: LiveUpdatePayload | null = null;
const livePayloadListeners = new Set<() => void>();

/** Subscribes to payload publishes; returns an unsubscribe function. */
export function subscribeLivePayload(listener: () => void): () => void {
  livePayloadListeners.add(listener);
  return () => {
    livePayloadListeners.delete(listener);
  };
}

/** Sets the latest payload and notifies every subscriber. */
export function publishLivePayload(payload: LiveUpdatePayload): void {
  livePayload = payload;
  for (const listener of livePayloadListeners) {
    listener();
  }
}

/** Stable snapshot getter for the latest payload (null before the first publish). */
export function getLivePayload(): LiveUpdatePayload | null {
  return livePayload;
}

/** React binding for the chip: re-renders on every publish; getServerSnapshot
 *  makes SSR (renderToString) safe. */
export function useLivePayload(): LiveUpdatePayload | null {
  return useSyncExternalStore(subscribeLivePayload, getLivePayload, getLivePayload);
}

/** Stream binding: fires `listener` ONLY on NEW publishes — never on mount —
 *  so a stale last payload is never re-applied to a freshly mounted page. */
export function useLivePayloadStream(listener: (payload: LiveUpdatePayload) => void): void {
  const listenerRef = useRef(listener);
  listenerRef.current = listener;

  useEffect(() => {
    return subscribeLivePayload(() => {
      if (livePayload) {
        listenerRef.current(livePayload);
      }
    });
  }, []);
}

/** Test seam: clears the payload and all subscribers. */
export function resetLivePayloadStore(): void {
  livePayload = null;
  livePayloadListeners.clear();
}

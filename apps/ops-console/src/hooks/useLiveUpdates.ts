import { useEffect, useRef } from 'react';

import type { ForecastPoint, InventoryOverviewRow, RouteScheduleSummary } from '../types/api';

export type LiveUpdatePayload = {
  type: 'live_update';
  server_time: string;
  inventory_overview: InventoryOverviewRow[];
  route_summaries: RouteScheduleSummary[];
  forecast_preview: ForecastPoint[];
};

type Props = {
  token: string | null;
  onMessage: (payload: LiveUpdatePayload) => void;
};

export function useLiveUpdates({ token, onMessage }: Props) {
  const socketRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    if (!token) return;

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
          onMessage(parsed);
        }
      } catch {
        // ignore malformed payloads
      }
    };

    return () => {
      socket.close();
    };
  }, [token, onMessage]);
}

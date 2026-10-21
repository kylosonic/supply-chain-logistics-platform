import { renderToString } from 'react-dom/server';
import { describe, expect, it, vi } from 'vitest';

const { getRunMock } = vi.hoisted(() => ({ getRunMock: vi.fn() }));

vi.mock('../services/logisticsApi', () => ({
  getRouteOptimizationRun: getRunMock,
}));

import { RouteHistoryExplanationState } from './RouteHistoryCard';
import { loadRouteHistoryDetail } from '../services/routeHistoryDetail';

describe('RouteHistoryCard explanation loading', () => {
  it('turns a failed history fetch into a visible error instead of an empty brief', async () => {
    getRunMock.mockRejectedValue(new Error('network unavailable'));

    const loaded = await loadRouteHistoryDetail('run-1');

    expect(loaded.detail).toBeNull();
    expect(loaded.error).toBe('network unavailable');

    const html = renderToString(
      <RouteHistoryExplanationState
        isLoading={false}
        error={loaded.error}
        detail={loaded.detail}
      />,
    ).replace(/<!-- -->/g, '');
    expect(html).toContain('network unavailable');
    expect(html).not.toContain('No explanation was recorded for this run.');
  });
});

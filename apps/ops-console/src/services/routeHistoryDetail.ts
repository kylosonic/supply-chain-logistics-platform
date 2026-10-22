import { apiErrorMessage } from './authErrors';
import { getRouteOptimizationRun } from './logisticsApi';
import type { RouteOptimizationRunDetail } from '../types/api';

export async function loadRouteHistoryDetail(
  runId: string,
): Promise<{ detail: RouteOptimizationRunDetail | null; error: string | null }> {
  try {
    return { detail: await getRouteOptimizationRun(runId), error: null };
  } catch (err) {
    return {
      detail: null,
      error: apiErrorMessage(err, 'Failed to load the route explanation.'),
    };
  }
}

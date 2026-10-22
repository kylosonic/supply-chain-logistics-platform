import { renderToString } from 'react-dom/server';
import { describe, expect, it } from 'vitest';

import { RouteDecisionBrief } from './RouteDecisionBrief';
import type { RouteDecisionExplanation } from '../types/api';

function strip(html: string): string {
  return html.replace(/<!-- -->/g, '');
}

function explanation(): RouteDecisionExplanation {
  return {
    method: 'deterministic_weighted_greedy',
    summary:
      'Travel time carried the largest share of the weighted objective (52.0%). The first stop was WH-002, with WH-003 the runner-up 1.20 weighted points behind.',
    dominant_factor: 'time',
    factor_share_pct: { distance: 35, time: 52, cost: 13 },
    constraints: ['Vehicle capacity (180 units) excluded 1 candidate stop during assignment.'],
    decision_points: [
      {
        sequence: 1,
        chosen_warehouse_code: 'WH-002',
        chosen_weighted_cost: 8.2,
        runner_up_warehouse_code: 'WH-003',
        runner_up_weighted_cost: 9.4,
        margin: 1.2,
        dominant_factor: 'time',
        capacity_excluded_count: 1,
        reason:
          'Travel time contributed 52.0% of the chosen leg\'s weighted score. WH-003 was the runner-up, 1.20 weighted points behind.',
      },
    ],
    runner_up: {
      first_stop_warehouse_code: 'WH-003',
      total_distance_km: 18.4,
      estimated_duration_min: 31,
      total_cost: 27.6,
      distance_delta_km: 2.4,
      duration_delta_min: 4,
      cost_delta: 3.6,
      summary: 'Starting with WH-003 instead produced a route that is 2.40 km farther and 4 min slower.',
    },
    limitations: ['Explains each greedy choice; it does not prove global optimality.'],
  };
}

describe('RouteDecisionBrief', () => {
  it('renders grounded factors, constraints, runner-up, and decision evidence', () => {
    const html = strip(renderToString(<RouteDecisionBrief explanation={explanation()} />));

    expect(html).toContain('Travel time led this plan');
    expect(html).toContain('52.0%');
    expect(html).toContain('Vehicle capacity (180 units) excluded 1 candidate stop');
    expect(html).toContain('Runner-up scenario');
    expect(html).toContain('Starting with WH-003 instead');
    expect(html).toContain('Decision-by-decision evidence (1)');
    expect(html).toContain('WH-003 was the runner-up');
    expect(html).toContain('does not prove global optimality');
  });

  it('states honestly when an older run has no explanation', () => {
    const html = strip(renderToString(<RouteDecisionBrief explanation={null} />));

    expect(html).toContain('No explanation was recorded for this run.');
    expect(html).toContain('New optimizations include one automatically.');
  });
});

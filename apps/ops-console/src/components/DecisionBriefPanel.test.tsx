import { renderToString } from 'react-dom/server';
import { StaticRouter } from 'react-router';
import { describe, expect, it } from 'vitest';

import { DecisionBriefContent } from './DecisionBriefPanel';
import type { DecisionBrief } from '../types/api';

function brief(overrides: Partial<DecisionBrief> = {}): DecisionBrief {
  return {
    generated_at: '2026-10-21T08:00:00Z',
    generated_by: 'grounded_rules',
    headline: '2 operating risk(s) need review. 2 recommended action(s) are available.',
    what_changed: ['1 open exception(s) are in the queue.'],
    risks: [
      {
        kind: 'cash_exposure',
        severity: 'high',
        message: '1 driver(s) have open cash exposure.',
        evidence: [{ record_type: 'cash', record_id: null, label: 'expected outstanding', value: '1500.00' }],
      },
    ],
    actions: [
      {
        priority: 1,
        action: 'Reconcile the top cash exposure before closing the day.',
        reason: 'Brief Driver has 1500.00 ETB outstanding.',
        href: '/dispatch',
        evidence: [{ record_type: 'cash', record_id: null, label: 'shortfall', value: '1500.00' }],
      },
    ],
    cash_risk: [
      {
        driver_id: 'driver-1',
        driver_name: 'Brief Driver',
        outstanding_count: 1,
        expected_etb: '1500.00',
        collected_etb: '0.00',
        shortfall_etb: '1500.00',
        risk_score: 50,
        factors: ['cash shortfall'],
      },
    ],
    triage: [
      {
        alert_id: 'alert-1',
        title: 'Customer has not confirmed receipt',
        severity: 'critical',
        age_hours: 2.5,
        priority: 74,
        suggested_action: 'Call the customer and confirm the delivery window.',
        evidence: [{ record_type: 'alert', record_id: 'alert-1', label: 'alert', value: null }],
      },
    ],
    ...overrides,
  };
}

function render(data: DecisionBrief): string {
  return renderToString(
    <StaticRouter location="/">
      <DecisionBriefContent brief={data} />
    </StaticRouter>,
  ).replace(/<!-- -->/g, '');
}

describe('DecisionBriefPanel evidence rendering', () => {
  it('renders the grounded risks, actions, cash radar, and triage evidence', () => {
    const html = render(brief());

    expect(html).toContain('2 operating risk(s) need review');
    expect(html).toContain('cash exposure');
    expect(html).toContain('expected outstanding: 1500.00');
    expect(html).toContain('Brief Driver');
    expect(html).toContain('50/100');
    expect(html).toContain('Customer has not confirmed receipt');
    expect(html).toContain('2.5h open');
    expect(html).toContain('Source: grounded_rules');
  });

  it('does not turn an empty fact bundle into a recommendation', () => {
    const html = render(
      brief({
        headline: '0 operating risk(s) need review. 0 recommended action(s) are available.',
        what_changed: [],
        risks: [],
        actions: [],
        cash_risk: [],
        triage: [],
      }),
    );

    expect(html).toContain('No grounded operating risk is currently recorded.');
    expect(html).toContain('No action is recommended from the current records.');
    expect(html).toContain('No open driver cash exposure is recorded.');
    expect(html).toContain('No open exception needs triage.');
  });

  it('shows a fail-closed state when the brief cannot be loaded', () => {
    const html = renderToString(
      <StaticRouter location="/">
        <DecisionBriefContent error={new Error('network')} />
      </StaticRouter>,
    );

    expect(html).toContain('No recommendation is being shown.');
  });
});

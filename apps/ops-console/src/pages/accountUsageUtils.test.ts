import { describe, expect, it } from 'vitest';

import {
  includedTasksLabel,
  overageRateLabel,
  usageMetricLabel,
  usageProgressPercent,
} from './accountUsageUtils';
import type { SubscriptionPlan, UsageSummary } from '../types/api';

const starterPlan: SubscriptionPlan = {
  tier: 'starter',
  title: 'Starter',
  monthly_price_usd: 399,
  seat_limit: 3,
  vehicle_limit: 25,
  included_tasks_per_month: 2500,
  overage_unit_price_usd: 0.2,
  includes_sso: false,
  includes_priority_support: false,
};

const usage: UsageSummary = {
  metric: 'delivery_tasks',
  period_start: '2026-07-01',
  period_end: '2026-07-31',
  included_units: 2500,
  used_units: 2100,
  overage_units: 0,
  utilization_percent: 84,
  estimated_overage_cost_usd: 0,
};

describe('accountUsageUtils', () => {
  it('maps delivery metric to friendly label', () => {
    expect(usageMetricLabel(usage)).toBe('Delivery tasks this billing month');
  });

  it('returns fallback label when usage is missing', () => {
    expect(usageMetricLabel(null)).toBe('Usage metrics unavailable');
  });

  it('caps usage progress percent at 100', () => {
    expect(usageProgressPercent({ ...usage, utilization_percent: 160 })).toBe(100);
  });

  it('returns 0 progress when utilization is null', () => {
    expect(usageProgressPercent({ ...usage, utilization_percent: null })).toBe(0);
  });

  it('formats included task quota and overage rate', () => {
    expect(includedTasksLabel(starterPlan)).toBe('2,500');
    expect(overageRateLabel(starterPlan)).toBe('$0.20 / task');
  });

  it('supports unlimited and custom overage labels', () => {
    const enterprisePlan: SubscriptionPlan = {
      ...starterPlan,
      tier: 'enterprise',
      monthly_price_usd: null,
      included_tasks_per_month: null,
      overage_unit_price_usd: null,
    };

    expect(includedTasksLabel(enterprisePlan)).toBe('Unlimited');
    expect(overageRateLabel(enterprisePlan)).toBe('N/A');
  });
});
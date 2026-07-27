import type { SubscriptionPlan, UsageSummary } from '../types/api';

export function usageMetricLabel(usage: UsageSummary | null): string {
  if (!usage) {
    return 'Usage metrics unavailable';
  }
  if (usage.metric === 'delivery_tasks') {
    return 'Delivery tasks this billing month';
  }
  return usage.metric;
}

export function usageProgressPercent(usage: UsageSummary | null): number {
  if (!usage?.utilization_percent) {
    return 0;
  }
  return Math.min(usage.utilization_percent, 100);
}

export function includedTasksLabel(plan: SubscriptionPlan): string {
  if (plan.included_tasks_per_month == null) {
    return 'Unlimited';
  }
  return plan.included_tasks_per_month.toLocaleString();
}

export function overageRateLabel(plan: SubscriptionPlan): string {
  if (plan.overage_unit_price_usd == null) {
    return 'N/A';
  }
  return `$${plan.overage_unit_price_usd.toFixed(2)} / task`;
}
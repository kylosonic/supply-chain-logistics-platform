import { useEffect, useMemo, useState } from 'react';
import type { FormEvent } from 'react';

import { MetricTile } from '../components/ui/MetricTile';
import { PageHeader } from '../components/ui/PageHeader';
import { Panel } from '../components/ui/Panel';
import { StatusBadge } from '../components/ui/StatusBadge';
import { WorkspaceResetDangerZone } from '../components/WorkspaceResetDangerZone';
import { useAuth } from '../context/AuthContext';
import {
  createProviderKey,
  getCurrentUsage,
  getCurrentSubscription,
  getProviderPreference,
  listPlans,
  listProviderKeys,
  revokeProviderKey,
  selectTier,
  setProviderPreference,
  testProviderKey,
} from '../services/billingApi';
import { getAuditTimeline } from '../services/logisticsApi';
import { includedTasksLabel, overageRateLabel, usageMetricLabel, usageProgressPercent } from './accountUsageUtils';
import type { AuditEvent, CurrentSubscription, ProviderKey, SubscriptionPlan, SubscriptionTier, UsageSummary } from '../types/api';

function priceText(plan: SubscriptionPlan): string {
  if (plan.monthly_price_usd == null) {
    return 'Contact sales';
  }
  return `$${plan.monthly_price_usd}/mo`;
}

function keyTone(status: string) {
  if (status === 'active') return 'success';
  if (status === 'revoked') return 'danger';
  return 'neutral';
}

export function AccountPage() {
  const { user } = useAuth();
  const [plans, setPlans] = useState<SubscriptionPlan[]>([]);
  const [subscription, setSubscription] = useState<CurrentSubscription | null>(null);
  const [usage, setUsage] = useState<UsageSummary | null>(null);
  const [keys, setKeys] = useState<ProviderKey[]>([]);
  const [auditEvents, setAuditEvents] = useState<AuditEvent[]>([]);
  const [providerName, setProviderName] = useState('openai');
  const [keyName, setKeyName] = useState('primary');
  const [apiKey, setApiKey] = useState('');
  const [preferredKeyId, setPreferredKeyId] = useState<string>('');
  const [statusMessage, setStatusMessage] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const currentTier = subscription?.tier;

  async function refresh() {
    const [plansData, subData, keysData, preference, auditData] = await Promise.all([
      listPlans(),
      getCurrentSubscription(),
      listProviderKeys(),
      getProviderPreference(),
      getAuditTimeline().catch(() => []),
    ]);

    setPlans(plansData);
    setSubscription(subData);
    setKeys(keysData);
    setPreferredKeyId(preference.key_id || '');
    setAuditEvents(auditData);

    try {
      const usageData = await getCurrentUsage();
      setUsage(usageData);
    } catch {
      setUsage(null);
    }
  }

  useEffect(() => {
    let mounted = true;
    (async () => {
      setLoading(true);
      try {
        await refresh();
      } catch {
        if (mounted) {
          setStatusMessage('Unable to load account settings.');
        }
      } finally {
        if (mounted) {
          setLoading(false);
        }
      }
    })();
    return () => {
      mounted = false;
    };
  }, []);

  async function onSelectTier(tier: SubscriptionTier) {
    setStatusMessage(null);
    try {
      const updated = await selectTier(tier);
      setSubscription(updated);
      setStatusMessage(`Subscription updated to ${updated.tier}.`);
    } catch {
      setStatusMessage('Failed to update subscription tier.');
    }
  }

  async function onAddKey(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setStatusMessage(null);
    try {
      await createProviderKey({ provider_name: providerName, key_name: keyName, api_key: apiKey });
      setApiKey('');
      await refresh();
      setStatusMessage('Provider key added successfully.');
    } catch {
      setStatusMessage('Failed to add provider key.');
    }
  }

  async function onTestKey(keyId: string) {
    setStatusMessage(null);
    try {
      const result = await testProviderKey(keyId);
      setStatusMessage(result.message);
    } catch {
      setStatusMessage('Failed to test provider key.');
    }
  }

  async function onRevokeKey(keyId: string) {
    setStatusMessage(null);
    try {
      await revokeProviderKey(keyId);
      await refresh();
      setStatusMessage('Provider key revoked.');
    } catch {
      setStatusMessage('Failed to revoke provider key.');
    }
  }

  async function onSetPreferredKey() {
    if (!preferredKeyId) {
      setStatusMessage('Select an active key first.');
      return;
    }
    setStatusMessage(null);
    try {
      const updated = await setProviderPreference(preferredKeyId);
      setStatusMessage(`Preferred AI provider set to ${updated.provider_name}.`);
      await refresh();
    } catch {
      setStatusMessage('Failed to update preferred AI provider.');
    }
  }

  async function onRefreshUsage() {
    setStatusMessage(null);
    try {
      const usageData = await getCurrentUsage();
      setUsage(usageData);
    } catch {
      setStatusMessage('Failed to refresh usage data.');
    }
  }

  const tierLabel = useMemo(() => {
    if (!subscription) return 'Unknown';
    return `${subscription.tier} (${subscription.status})`;
  }, [subscription]);

  const progressPercent = useMemo(() => usageProgressPercent(usage), [usage]);
  const metricLabel = useMemo(() => usageMetricLabel(usage), [usage]);
  const activeKeyCount = useMemo(() => keys.filter((key) => key.status === 'active').length, [keys]);

  const fieldClassName =
    'glow-ring min-h-12 rounded-2xl border border-slate-700 bg-slate-900/80 px-4 text-sm text-slate-100 outline-none transition focus:border-sky-400/50';

  if (loading) {
    return (
      <div className="space-y-5">
        <div className="skeleton h-[140px] rounded-[30px]" />
        <div className="grid grid-cols-1 gap-4 xl:grid-cols-4">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="skeleton h-[130px] rounded-[24px]" />
          ))}
        </div>
        <div className="grid grid-cols-1 gap-5 xl:grid-cols-2">
          <div className="skeleton h-[400px] rounded-[28px]" />
          <div className="skeleton h-[400px] rounded-[28px]" />
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Workspace controls"
        title="Billing, quota, and AI provider governance"
        description="Keep subscription posture, included task capacity, overage pressure, and provider configuration visible to the team running the workspace."
      />

      <div className="grid grid-cols-1 gap-4 xl:grid-cols-4">
        <MetricTile title="Current plan" value={subscription?.tier ?? 'Unknown'} detail={`Status: ${subscription?.status ?? 'unknown'}`} tone="info" />
        <MetricTile title="Usage" value={usage ? `${usage.used_units.toLocaleString()}` : 'N/A'} detail={metricLabel} tone={progressPercent >= 100 ? 'danger' : progressPercent >= 80 ? 'warning' : 'success'} />
        <MetricTile title="Preferred provider" value={subscription?.preferred_ai_provider ?? 'None'} detail="Dashboard workflows use this provider when configured." tone="neutral" />
        <MetricTile title="Active keys" value={activeKeyCount} detail="Provider credentials available for current workspace use." tone={activeKeyCount > 0 ? 'success' : 'warning'} />
      </div>

      {statusMessage ? (
        <Panel className="border-sky-500/20 bg-sky-950/12">
          <p className="text-sm text-sky-100">{statusMessage}</p>
        </Panel>
      ) : null}

      <div className="grid grid-cols-1 gap-5 xl:grid-cols-[1.05fr_0.95fr]">
        <Panel
          eyebrow="Subscription"
          title="Current plan and usage posture"
          description="Switch tiers, monitor included task capacity, and keep the commercial model legible to workspace operators."
          actions={
            <button
              type="button"
              onClick={onRefreshUsage}
              className="inline-flex min-h-10 items-center justify-center rounded-full border border-slate-700 px-4 text-sm font-semibold text-slate-200 transition hover:border-slate-500 hover:bg-slate-900"
            >
              Refresh usage
            </button>
          }
        >
          <div className="rounded-[22px] border border-slate-800 bg-slate-900/70 p-4">
            <p className="text-sm font-semibold text-slate-100">Current plan: {tierLabel}</p>
            <p className="mt-2 text-sm text-slate-400">Organization: {subscription?.organization_name ?? 'Unknown'}</p>
          </div>

          <div className="mt-4 rounded-[22px] border border-slate-800 bg-slate-900/70 p-4">
            <p className="text-sm font-semibold text-slate-100">Usage meter</p>
            <p className="mt-1 text-xs text-slate-500">{metricLabel}</p>

            {usage ? (
              <div className="mt-4 space-y-4">
                <div className="grid gap-2 text-xs text-slate-400 md:grid-cols-3">
                  <p>
                    Period: <span className="font-semibold text-slate-200">{usage.period_start}</span> to{' '}
                    <span className="font-semibold text-slate-200">{usage.period_end}</span>
                  </p>
                  <p>
                    Used: <span className="font-semibold text-slate-200">{usage.used_units.toLocaleString()}</span>
                  </p>
                  <p>
                    Included:{' '}
                    <span className="font-semibold text-slate-200">
                      {usage.included_units == null ? 'Unlimited' : usage.included_units.toLocaleString()}
                    </span>
                  </p>
                </div>

                {usage.included_units != null ? (
                  <>
                    <div className="h-2 overflow-hidden rounded-full bg-slate-800">
                      <div className="h-full rounded-full bg-gradient-to-r from-sky-300 via-sky-400 to-teal-300" style={{ width: `${progressPercent}%` }} />
                    </div>
                    <p className="text-xs text-slate-400">
                      Utilization: <span className="font-semibold text-slate-200">{usage.utilization_percent ?? 0}%</span>
                    </p>
                  </>
                ) : (
                  <p className="text-xs text-slate-400">No monthly cap on this plan.</p>
                )}

                <div className="grid gap-2 text-xs text-slate-400 md:grid-cols-2">
                  <p>
                    Overage units: <span className="font-semibold text-slate-200">{usage.overage_units.toLocaleString()}</span>
                  </p>
                  <p>
                    Estimated overage cost:{' '}
                    <span className="font-semibold text-slate-200">
                      {usage.estimated_overage_cost_usd == null
                        ? 'N/A'
                        : `$${usage.estimated_overage_cost_usd.toLocaleString()}`}
                    </span>
                  </p>
                </div>
              </div>
            ) : (
              <p className="mt-4 text-xs text-slate-400">Usage endpoint unavailable. Run the latest backend migration and refresh.</p>
            )}
          </div>

          <div className="mt-4 grid gap-3 md:grid-cols-3">
            {plans.map((plan) => (
              <div key={plan.tier} className="hover-lift rounded-[22px] border border-slate-800 bg-slate-900/70 p-4 transition">
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <h2 className="font-['Space_Grotesk'] text-xl font-semibold text-slate-50">{plan.title}</h2>
                    <p className="text-sm text-slate-400">{priceText(plan)}</p>
                  </div>
                  {currentTier === plan.tier ? <StatusBadge label="Current" tone="info" /> : null}
                </div>
                <div className="mt-3 space-y-1 text-xs text-slate-400">
                  <p>Seats: {plan.seat_limit ?? 'Unlimited'}</p>
                  <p>Vehicles: {plan.vehicle_limit ?? 'Unlimited'}</p>
                  <p>Included tasks: {includedTasksLabel(plan)}</p>
                  <p>Overage rate: {overageRateLabel(plan)}</p>
                </div>
                <button
                  type="button"
                  disabled={currentTier === plan.tier}
                  onClick={() => onSelectTier(plan.tier)}
                  className="mt-4 inline-flex min-h-11 items-center justify-center rounded-full border border-slate-700 px-4 text-xs font-semibold text-slate-200 transition hover:border-slate-500 hover:bg-slate-950 disabled:cursor-not-allowed disabled:opacity-50"
                >
                  {currentTier === plan.tier ? 'Current plan' : 'Switch to plan'}
                </button>
              </div>
            ))}
          </div>
        </Panel>

        <Panel
          eyebrow="AI provider control"
          title="Bring your own provider keys"
          description="Set the preferred provider for dashboard workflows, test active keys, and rotate credentials without leaving the workspace."
        >
          <div className="rounded-[22px] border border-slate-800 bg-slate-900/70 p-4">
            <p className="text-sm font-semibold text-slate-100">Preferred AI provider for the dashboard</p>
            <div className="mt-3 flex flex-wrap items-center gap-3">
              <select value={preferredKeyId} onChange={(event) => setPreferredKeyId(event.target.value)} className={`${fieldClassName} min-w-[240px]`}>
                <option value="">Select active provider key</option>
                {keys
                  .filter((key) => key.status === 'active')
                  .map((key) => (
                    <option key={key.id} value={key.id}>{`${key.provider_name} - ${key.key_name} (${key.masked_key})`}</option>
                  ))}
              </select>
              <button
                type="button"
                onClick={onSetPreferredKey}
                className="inline-flex min-h-12 items-center justify-center rounded-full bg-gradient-to-r from-sky-300 via-sky-400 to-teal-300 px-5 text-sm font-semibold text-slate-950 transition hover:brightness-105"
              >
                Save preferred provider
              </button>
            </div>
            <p className="mt-2 text-xs text-slate-500">Current: {subscription?.preferred_ai_provider ?? 'Not configured'}</p>
          </div>

          <form onSubmit={onAddKey} className="mt-4 grid gap-3 md:grid-cols-3">
            <input value={providerName} onChange={(event) => setProviderName(event.target.value)} className={fieldClassName} placeholder="Provider name" />
            <input value={keyName} onChange={(event) => setKeyName(event.target.value)} className={fieldClassName} placeholder="Key label" />
            <input value={apiKey} onChange={(event) => setApiKey(event.target.value)} className={fieldClassName} placeholder="API key" />
            <div className="md:col-span-3">
              <button type="submit" className="inline-flex min-h-12 items-center justify-center rounded-full bg-gradient-to-r from-sky-300 via-sky-400 to-teal-300 px-5 text-sm font-semibold text-slate-950 transition hover:brightness-105">
                Save key
              </button>
            </div>
          </form>

          <div className="mt-4 space-y-3">
            {keys.map((key) => (
              <article key={key.id} className="animate-fade-in hover-lift rounded-[22px] border border-slate-800 bg-slate-900/70 p-4">
                <div className="flex flex-wrap items-start justify-between gap-3">
                  <div>
                    <div className="flex flex-wrap items-center gap-2">
                      <StatusBadge label={key.status} tone={keyTone(key.status)} />
                      <span className="text-xs uppercase tracking-[0.18em] text-slate-500">{key.provider_name}</span>
                    </div>
                    <h3 className="mt-2 font-['Space_Grotesk'] text-lg font-semibold text-slate-50">{key.key_name}</h3>
                    <p className="mt-1 font-mono text-xs text-slate-400">{key.masked_key}</p>
                  </div>
                  <div className="flex flex-wrap gap-2">
                    <button
                      type="button"
                      onClick={() => onTestKey(key.id)}
                      className="rounded-full border border-slate-700 px-3 py-2 text-xs font-semibold text-slate-200 transition hover:border-slate-500 hover:bg-slate-950"
                    >
                      Test
                    </button>
                    {key.status === 'active' ? (
                      <button
                        type="button"
                        onClick={() => onRevokeKey(key.id)}
                        className="rounded-full border border-rose-500/30 px-3 py-2 text-xs font-semibold text-rose-200 transition hover:border-rose-400/50 hover:bg-rose-950/20"
                      >
                        Revoke
                      </button>
                    ) : null}
                  </div>
                </div>
              </article>
            ))}

            {keys.length === 0 ? <p className="text-sm text-slate-500">No provider keys configured yet.</p> : null}
          </div>
        </Panel>
      </div>

      <Panel
        eyebrow="Audit timeline"
        title="Recent workspace events"
        description="Subscription changes, provider-key actions, routing decisions, and planning events are recorded here for operator review."
      >
        <div className="space-y-3">
          {auditEvents.slice(0, 8).map((event) => (
            <article key={event.id} className="animate-fade-in hover-lift rounded-[22px] border border-slate-800 bg-slate-900/70 p-4">
              <div className="flex flex-wrap items-center justify-between gap-3">
                <div>
                  <div className="flex flex-wrap items-center gap-2">
                    <StatusBadge label={event.entity_type} tone="info" />
                    <span className="text-xs uppercase tracking-[0.18em] text-slate-500">{event.event_type}</span>
                  </div>
                  <h3 className="mt-2 font-['Space_Grotesk'] text-lg font-semibold text-slate-50">{event.description}</h3>
                </div>
                <span className="text-xs text-slate-500">{new Date(event.created_at).toLocaleString()}</span>
              </div>
            </article>
          ))}

          {auditEvents.length === 0 ? <p className="text-sm text-slate-500">No audit events recorded yet.</p> : null}
        </div>
      </Panel>

      {user?.role === 'admin' ? (
        <WorkspaceResetDangerZone
          organizationName={subscription?.organization_name ?? ''}
          isAdmin
        />
      ) : null}
    </div>
  );
}

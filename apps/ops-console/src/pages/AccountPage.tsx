import { useEffect, useMemo, useState } from 'react';
import type { FormEvent } from 'react';

import {
  createProviderKey,
  getCurrentSubscription,
  getProviderPreference,
  listPlans,
  listProviderKeys,
  revokeProviderKey,
  selectTier,
  setProviderPreference,
  testProviderKey,
} from '../services/billingApi';
import type { CurrentSubscription, ProviderKey, SubscriptionPlan, SubscriptionTier } from '../types/api';

function priceText(plan: SubscriptionPlan): string {
  if (plan.monthly_price_usd == null) {
    return 'Contact sales';
  }
  return `$${plan.monthly_price_usd}/mo`;
}

export function AccountPage() {
  const [plans, setPlans] = useState<SubscriptionPlan[]>([]);
  const [subscription, setSubscription] = useState<CurrentSubscription | null>(null);
  const [keys, setKeys] = useState<ProviderKey[]>([]);
  const [providerName, setProviderName] = useState('openai');
  const [keyName, setKeyName] = useState('primary');
  const [apiKey, setApiKey] = useState('');
  const [preferredKeyId, setPreferredKeyId] = useState<string>('');
  const [statusMessage, setStatusMessage] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const currentTier = subscription?.tier;

  async function refresh() {
    const [plansData, subData, keysData, preference] = await Promise.all([
      listPlans(),
      getCurrentSubscription(),
      listProviderKeys(),
      getProviderPreference(),
    ]);
    setPlans(plansData);
    setSubscription(subData);
    setKeys(keysData);
    setPreferredKeyId(preference.key_id || '');
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

  const tierLabel = useMemo(() => {
    if (!subscription) return 'Unknown';
    return `${subscription.tier} (${subscription.status})`;
  }, [subscription]);

  if (loading) {
    return <div className="rounded-xl border border-slate-200 bg-white p-6 text-sm text-slate-600">Loading account settings...</div>;
  }

  return (
    <div className="space-y-6">
      <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
        <h1 className="text-xl font-semibold text-slate-900">Account and Billing</h1>
        <p className="mt-1 text-sm text-slate-600">Manage your plan and team entitlements.</p>
        <div className="mt-4 rounded-lg border border-slate-200 bg-slate-50 p-4 text-sm">
          <p className="font-medium text-slate-800">Current plan: {tierLabel}</p>
          <p className="text-slate-600">Organization: {subscription?.organization_name ?? 'Unknown'}</p>
        </div>
        <div className="mt-4 grid gap-3 md:grid-cols-3">
          {plans.map((plan) => (
            <div key={plan.tier} className="rounded-xl border border-slate-200 p-4">
              <h2 className="font-semibold text-slate-900">{plan.title}</h2>
              <p className="text-sm text-slate-600">{priceText(plan)}</p>
              <p className="mt-2 text-xs text-slate-500">Seats: {plan.seat_limit ?? 'Unlimited'}</p>
              <p className="text-xs text-slate-500">Vehicles: {plan.vehicle_limit ?? 'Unlimited'}</p>
              <button
                type="button"
                disabled={currentTier === plan.tier}
                onClick={() => onSelectTier(plan.tier)}
                className="mt-3 rounded-md bg-slate-900 px-3 py-2 text-xs font-semibold text-white disabled:cursor-not-allowed disabled:bg-slate-400"
              >
                {currentTier === plan.tier ? 'Current plan' : 'Switch to plan'}
              </button>
            </div>
          ))}
        </div>
      </section>

      <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
        <h2 className="text-lg font-semibold text-slate-900">Bring Your Own AI Keys</h2>
        <p className="mt-1 text-sm text-slate-600">Connect your preferred AI providers securely.</p>

        <div className="mt-4 rounded-lg border border-slate-200 bg-slate-50 p-4">
          <p className="text-sm font-semibold text-slate-800">Preferred AI provider for the dashboard</p>
          <div className="mt-2 flex flex-wrap items-center gap-2">
            <select
              value={preferredKeyId}
              onChange={(event) => setPreferredKeyId(event.target.value)}
              className="min-w-[220px] rounded-md border border-slate-300 px-3 py-2 text-sm"
            >
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
              className="rounded-md bg-slate-900 px-4 py-2 text-sm font-semibold text-white"
            >
              Save preferred provider
            </button>
          </div>
          <p className="mt-2 text-xs text-slate-600">
            Current: {subscription?.preferred_ai_provider ?? 'Not configured'}
          </p>
        </div>

        <form onSubmit={onAddKey} className="mt-4 grid gap-3 md:grid-cols-3">
          <input
            value={providerName}
            onChange={(event) => setProviderName(event.target.value)}
            className="rounded-md border border-slate-300 px-3 py-2 text-sm"
            placeholder="Provider name"
          />
          <input
            value={keyName}
            onChange={(event) => setKeyName(event.target.value)}
            className="rounded-md border border-slate-300 px-3 py-2 text-sm"
            placeholder="Key label"
          />
          <input
            value={apiKey}
            onChange={(event) => setApiKey(event.target.value)}
            className="rounded-md border border-slate-300 px-3 py-2 text-sm"
            placeholder="API key"
          />
          <div className="md:col-span-3">
            <button type="submit" className="rounded-md bg-slate-900 px-4 py-2 text-sm font-semibold text-white">
              Save key
            </button>
          </div>
        </form>

        <div className="mt-4 overflow-x-auto">
          <table className="w-full min-w-[520px] divide-y divide-slate-200 text-sm">
            <thead className="bg-slate-50 text-left text-xs uppercase tracking-wide text-slate-500">
              <tr>
                <th className="px-3 py-2">Provider</th>
                <th className="px-3 py-2">Key name</th>
                <th className="px-3 py-2">Masked key</th>
                <th className="px-3 py-2">Status</th>
                <th className="px-3 py-2">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 bg-white">
              {keys.map((key) => (
                <tr key={key.id}>
                  <td className="px-3 py-2">{key.provider_name}</td>
                  <td className="px-3 py-2">{key.key_name}</td>
                  <td className="px-3 py-2 font-mono text-xs">{key.masked_key}</td>
                  <td className="px-3 py-2">{key.status}</td>
                  <td className="space-x-2 px-3 py-2">
                    <button
                      type="button"
                      onClick={() => onTestKey(key.id)}
                      className="rounded border border-slate-300 px-2 py-1 text-xs font-semibold text-slate-700"
                    >
                      Test
                    </button>
                    {key.status === 'active' ? (
                      <button
                        type="button"
                        onClick={() => onRevokeKey(key.id)}
                        className="rounded border border-red-200 px-2 py-1 text-xs font-semibold text-red-700"
                      >
                        Revoke
                      </button>
                    ) : null}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {statusMessage ? <p className="text-sm text-slate-700">{statusMessage}</p> : null}
    </div>
  );
}

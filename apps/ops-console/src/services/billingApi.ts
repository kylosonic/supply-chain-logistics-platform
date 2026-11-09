import { api } from './api';
import type {
  CurrentSubscription,
  ProviderKey,
  ProviderKeyTestResult,
  ProviderPreference,
  SubscriptionPlan,
  SubscriptionTier,
  UsageSummary,
} from '../types/api';

export async function listPlans(): Promise<SubscriptionPlan[]> {
  const { data } = await api.get<SubscriptionPlan[]>('/subscriptions/plans');
  return data;
}

export async function getCurrentSubscription(): Promise<CurrentSubscription> {
  const { data } = await api.get<CurrentSubscription>('/subscriptions/me');
  return data;
}

export async function selectTier(tier: SubscriptionTier): Promise<CurrentSubscription> {
  const { data } = await api.post<CurrentSubscription>('/subscriptions/select-tier', { tier });
  return data;
}

export async function updateContactPhone(contactPhone: string): Promise<CurrentSubscription> {
  const { data } = await api.post<CurrentSubscription>('/subscriptions/me/contact-phone', {
    contact_phone: contactPhone,
  });
  return data;
}

export async function listProviderKeys(): Promise<ProviderKey[]> {
  const { data } = await api.get<ProviderKey[]>('/providers/keys');
  return data;
}

export async function createProviderKey(payload: {
  provider_name: string;
  key_name: string;
  api_key: string;
}): Promise<ProviderKey> {
  const { data } = await api.post<ProviderKey>('/providers/keys', payload);
  return data;
}

export async function revokeProviderKey(keyId: string): Promise<ProviderKey> {
  const { data } = await api.post<ProviderKey>(`/providers/keys/${keyId}/revoke`, {});
  return data;
}

export async function testProviderKey(keyId: string): Promise<ProviderKeyTestResult> {
  const { data } = await api.post<ProviderKeyTestResult>(`/providers/keys/${keyId}/test`, {});
  return data;
}

export async function getProviderPreference(): Promise<ProviderPreference> {
  const { data } = await api.get<ProviderPreference>('/providers/preference');
  return data;
}

export async function setProviderPreference(keyId: string): Promise<ProviderPreference> {
  const { data } = await api.post<ProviderPreference>('/providers/preference', { key_id: keyId });
  return data;
}

export async function getCurrentUsage(): Promise<UsageSummary> {
  const { data } = await api.get<UsageSummary>('/subscriptions/usage/me');
  return data;
}


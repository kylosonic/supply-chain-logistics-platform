import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';

import {
  getInventoryOverview,
  getForecast,
  getRouteSchedules,
  listShipments,
  listAlerts,
  getExceptionFeed,
  getAuditTimeline,
  listReplenishmentPlans,
  getDockAppointments,
  getWeatherRiskZones,
  listProviderKeys,
  getRouteOptimizationHistory,
} from '../services/logisticsApi';
import { getCurrentUsage } from '../services/billingApi';
import { dismissPitch, getActivationState, resetWorkspace } from '../services/activationApi';
import { useAuth } from '../context/AuthContext';
import {
  getReceiptAuditEvents,
  getWallet,
  listReceiptQueue,
  listReceipts,
  listVerifiedAudit,
  removeTrustedPayer,
  renderDecision,
  reverseReceipt,
  submitDispute,
  undoReceipt,
} from '../services/receiptsApi';
import type { RenderDecisionPayload } from '../services/receiptsApi';

export function useInventoryOverview() {
  return useQuery({
    queryKey: ['inventory', 'overview'],
    queryFn: getInventoryOverview,
    staleTime: 30_000,
  });
}

export function useForecast(horizonWeeks = 4) {
  return useQuery({
    queryKey: ['forecast', horizonWeeks],
    queryFn: () => getForecast(horizonWeeks),
    staleTime: 60_000,
  });
}

export function useRouteSchedules() {
  return useQuery({
    queryKey: ['routes', 'schedules'],
    queryFn: getRouteSchedules,
    staleTime: 30_000,
  });
}

export function useShipments() {
  return useQuery({
    queryKey: ['shipments'],
    queryFn: listShipments,
    staleTime: 30_000,
  });
}

export function useAlerts(status?: string) {
  return useQuery({
    queryKey: ['alerts', status],
    queryFn: () => listAlerts(status as 'open' | 'acknowledged' | 'resolved' | undefined),
    staleTime: 30_000,
  });
}

export function useExceptionFeed() {
  return useQuery({
    queryKey: ['ops', 'exception-feed'],
    queryFn: getExceptionFeed,
    staleTime: 30_000,
  });
}

export function useAuditTimeline() {
  return useQuery({
    queryKey: ['ops', 'audit-timeline'],
    queryFn: getAuditTimeline,
    staleTime: 60_000,
  });
}

export function useReplenishmentPlans() {
  return useQuery({
    queryKey: ['planning', 'replenishment'],
    queryFn: listReplenishmentPlans,
    staleTime: 30_000,
  });
}

export function useCurrentUsage() {
  return useQuery({
    queryKey: ['subscriptions', 'usage'],
    queryFn: getCurrentUsage,
    staleTime: 60_000,
  });
}

export function useDockAppointments() {
  return useQuery({
    queryKey: ['ops', 'dock-appointments'],
    queryFn: getDockAppointments,
    staleTime: 60_000,
  });
}

export function useWeatherRiskZones() {
  return useQuery({
    queryKey: ['weather', 'risk-zones'],
    queryFn: getWeatherRiskZones,
    staleTime: 120_000,
  });
}

export function useProviderKeys() {
  return useQuery({
    queryKey: ['providers', 'keys'],
    queryFn: listProviderKeys,
    staleTime: 30_000,
  });
}

export function useRouteOptimizationHistory() {
  return useQuery({
    queryKey: ['routes', 'history'],
    queryFn: getRouteOptimizationHistory,
    staleTime: 30_000,
  });
}

export function useReceipts() {
  return useQuery({
    queryKey: ['receipts'],
    queryFn: listReceipts,
    staleTime: 15_000,
  });
}

export function useReceiptQueue() {
  return useQuery({
    queryKey: ['receipts', 'queue'],
    queryFn: listReceiptQueue,
    staleTime: 10_000,
  });
}

export function useWallet() {
  return useQuery({
    queryKey: ['receipts', 'wallet'],
    queryFn: getWallet,
    staleTime: 15_000,
  });
}

export function useRenderDecision() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, payload }: { id: string; payload: RenderDecisionPayload }) =>
      renderDecision(id, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['receipts'] });
    },
  });
}

export function useSubmitDispute() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, text }: { id: string; text: string }) => submitDispute(id, text),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['receipts'] });
    },
  });
}

export function useVerifiedAudit() {
  return useQuery({
    queryKey: ['receipts', 'audit'],
    queryFn: listVerifiedAudit,
    staleTime: 15_000,
  });
}

export function useReceiptAuditEvents(id: string | null) {
  return useQuery({
    queryKey: ['receipts', 'audit-events', id],
    queryFn: () => getReceiptAuditEvents(id as string),
    enabled: Boolean(id),
    staleTime: 15_000,
  });
}

function invalidateReversalSurfaces(queryClient: ReturnType<typeof useQueryClient>) {
  queryClient.invalidateQueries({ queryKey: ['receipts'] });
  queryClient.invalidateQueries({ queryKey: ['receipts', 'queue'] });
  queryClient.invalidateQueries({ queryKey: ['receipts', 'audit'] });
  queryClient.invalidateQueries({ queryKey: ['receipts', 'audit-events'] });
  queryClient.invalidateQueries({ queryKey: ['ops', 'audit-timeline'] });
}

export function useUndoReceipt() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, note }: { id: string; note?: string | null }) => undoReceipt(id, note),
    onSuccess: () => {
      invalidateReversalSurfaces(queryClient);
    },
  });
}

export function useReverseReceipt() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, reason }: { id: string; reason: string }) => reverseReceipt(id, reason),
    onSuccess: () => {
      invalidateReversalSurfaces(queryClient);
    },
  });
}

export function useRemoveTrustedPayer() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ senderName, organizationId }: { senderName: string; organizationId: string }) =>
      removeTrustedPayer(senderName, organizationId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['receipts', 'queue'] });
      queryClient.invalidateQueries({ queryKey: ['receipts', 'audit'] });
    },
  });
}

export function useInvalidateDashboard() {
  const queryClient = useQueryClient();
  return () => {
    queryClient.invalidateQueries({ queryKey: ['inventory'] });
    queryClient.invalidateQueries({ queryKey: ['forecast'] });
    queryClient.invalidateQueries({ queryKey: ['routes'] });
    queryClient.invalidateQueries({ queryKey: ['shipments'] });
    queryClient.invalidateQueries({ queryKey: ['subscriptions'] });
    queryClient.invalidateQueries({ queryKey: ['activation'] });
  };
}

// ---------------------------------------------------------------------------
// Phase 4 activation hooks (blueprint §9)
// ---------------------------------------------------------------------------

export function useActivationState() {
  return useQuery({
    queryKey: ['activation'],
    queryFn: getActivationState,
    staleTime: 30_000,
  });
}

export function useResetWorkspace() {
  const queryClient = useQueryClient();
  const { logout } = useAuth();
  return useMutation({
    mutationFn: (workspaceName: string) => resetWorkspace(workspaceName),
    onSuccess: async () => {
      // NB-35.7: clear auth state + server cookie, then land on /login;
      // the next login lands on `/` with the 0% banner (decision #10).
      queryClient.clear();
      await logout();
      window.location.assign('/login');
    },
  });
}

export function useDismissPitch() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (level: 'p60') => dismissPitch(level),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['activation'] });
    },
  });
}

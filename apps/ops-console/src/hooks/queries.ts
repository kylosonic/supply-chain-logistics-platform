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

export function useInvalidateDashboard() {
  const queryClient = useQueryClient();
  return () => {
    queryClient.invalidateQueries({ queryKey: ['inventory'] });
    queryClient.invalidateQueries({ queryKey: ['forecast'] });
    queryClient.invalidateQueries({ queryKey: ['routes'] });
    queryClient.invalidateQueries({ queryKey: ['shipments'] });
    queryClient.invalidateQueries({ queryKey: ['subscriptions'] });
  };
}

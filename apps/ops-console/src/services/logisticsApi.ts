import { api } from './api';
import type {
  Alert,
  AuditEvent,
  ExceptionFeedResponse,
  ForecastResponse,
  IngestionResult,
  InventoryOverviewRow,
  ReplenishmentPlan,
  RouteOptimizationRunDetail,
  RouteOptimizationRunSummary,
  RouteOptimizePayload,
  RouteOptimizeResponse,
  RouteScheduleSummary,
  Shipment,
  ShipmentStatus,
  WeatherRiskZone,
} from '../types/api';

export async function getWeatherRiskZones(): Promise<WeatherRiskZone[]> {
  const { data } = await api.get<WeatherRiskZone[]>('/weather/risk-zones');
  return data;
}

export async function getInventoryOverview(): Promise<InventoryOverviewRow[]> {
  const { data } = await api.get<InventoryOverviewRow[]>('/inventory/overview');
  return data;
}

export async function getForecast(horizonWeeks = 4): Promise<ForecastResponse> {
  const { data } = await api.post<ForecastResponse>('/forecast/weekly-demand', {
    horizon_weeks: horizonWeeks,
  });
  return data;
}

export async function getRouteSchedules(): Promise<RouteScheduleSummary[]> {
  const { data } = await api.get<RouteScheduleSummary[]>('/routes/schedules');
  return data;
}

export async function optimizeRoute(payload: RouteOptimizePayload): Promise<RouteOptimizeResponse> {
  const { data } = await api.post<RouteOptimizeResponse>('/routes/optimize', payload);
  return data;
}

export async function getRouteOptimizationHistory(): Promise<RouteOptimizationRunSummary[]> {
  const { data } = await api.get<RouteOptimizationRunSummary[]>('/routes/history');
  return data;
}

export async function getRouteOptimizationRun(runId: string): Promise<RouteOptimizationRunDetail> {
  const { data } = await api.get<RouteOptimizationRunDetail>(`/routes/history/${runId}`);
  return data;
}

function toCsvFormData(file: File): FormData {
  const formData = new FormData();
  formData.append('file', file);
  return formData;
}

export async function uploadWarehousesCsv(file: File): Promise<IngestionResult> {
  const { data } = await api.post<IngestionResult>('/ingestion/warehouses-csv', toCsvFormData(file), {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return data;
}

export async function uploadItemsCsv(file: File): Promise<IngestionResult> {
  const { data } = await api.post<IngestionResult>('/ingestion/items-csv', toCsvFormData(file), {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return data;
}

export async function uploadFleetAssetsCsv(file: File): Promise<IngestionResult> {
  const { data } = await api.post<IngestionResult>('/ingestion/fleet-assets-csv', toCsvFormData(file), {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return data;
}

export async function uploadInventoryCsv(file: File): Promise<IngestionResult> {
  const formData = toCsvFormData(file);
  const { data } = await api.post('/ingestion/inventory-csv', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return data;
}

export async function uploadOrdersCsv(file: File): Promise<IngestionResult> {
  const { data } = await api.post<IngestionResult>('/ingestion/orders-csv', toCsvFormData(file), {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return data;
}

export async function listShipments(): Promise<Shipment[]> {
  const { data } = await api.get<Shipment[]>('/shipments');
  return data;
}

export async function createShipment(payload: {
  shipment_no: string;
  origin_warehouse_code: string;
  destination_warehouse_code: string;
  sku: string;
  quantity_units: number;
  planned_departure?: string;
  expected_delivery?: string;
}) {
  const { data } = await api.post<Shipment>('/shipments', payload);
  return data;
}

export async function updateShipmentStatus(
  shipmentId: string,
  payload: {
    status: ShipmentStatus;
    delay_reason?: string;
    last_known_location?: string;
    proof_of_delivery_ref?: string;
  },
) {
  const { data } = await api.post<Shipment>(`/shipments/${shipmentId}/status`, payload);
  return data;
}

export async function listAlerts(status?: 'open' | 'acknowledged' | 'resolved'): Promise<Alert[]> {
  const { data } = await api.get<Alert[]>('/alerts', {
    params: status ? { status } : undefined,
  });
  return data;
}

export async function createAlert(payload: {
  title: string;
  message: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
}) {
  const { data } = await api.post<Alert>('/alerts', {
    alert_type: 'manual',
    ...payload,
  });
  return data;
}

export async function scanAlerts(): Promise<Alert[]> {
  const { data } = await api.post<Alert[]>('/alerts/scan');
  return data;
}

export async function acknowledgeAlert(alertId: string, note?: string) {
  const { data } = await api.post<Alert>(`/alerts/${alertId}/acknowledge`, { note });
  return data;
}

export async function resolveAlert(alertId: string, note?: string) {
  const { data } = await api.post<Alert>(`/alerts/${alertId}/resolve`, { note });
  return data;
}

export async function autoResolveAlert(alertId: string) {
  const { data } = await api.post<Alert>(`/alerts/${alertId}/auto-resolve`);
  return data;
}

export async function getExceptionFeed(): Promise<ExceptionFeedResponse> {
  const { data } = await api.get<ExceptionFeedResponse>('/ops/exception-feed');
  return data;
}

export async function getAuditTimeline(): Promise<AuditEvent[]> {
  const { data } = await api.get<AuditEvent[]>('/ops/audit-timeline');
  return data;
}

export async function listReplenishmentPlans(): Promise<ReplenishmentPlan[]> {
  const { data } = await api.get<ReplenishmentPlan[]>('/planning/replenishment');
  return data;
}

export async function generateReplenishmentPlans(horizonWeeks: number): Promise<ReplenishmentPlan[]> {
  const { data } = await api.post<ReplenishmentPlan[]>('/planning/replenishment/generate', {
    horizon_weeks: horizonWeeks,
  });
  return data;
}

export async function approveReplenishmentPlan(planId: string, approvedQuantity?: number, note?: string) {
  const { data } = await api.post<ReplenishmentPlan>(`/planning/replenishment/${planId}/approve`, {
    approved_quantity: approvedQuantity,
    note,
  });
  return data;
}

export async function rejectReplenishmentPlan(planId: string, reason: string) {
  const { data } = await api.post<ReplenishmentPlan>(`/planning/replenishment/${planId}/reject`, { reason });
  return data;
}

export async function listProviderKeys(): Promise<import('../types/api').ProviderKey[]> {
  const { data } = await api.get<import('../types/api').ProviderKey[]>('/providers/keys');
  return data;
}

export async function createProviderKey(payload: { provider_name: string; key_name: string; api_key: string }) {
  const { data } = await api.post<import('../types/api').ProviderKey>('/providers/keys', payload);
  return data;
}

export async function testProviderKey(keyId: string) {
  const { data } = await api.post<import('../types/api').ProviderKeyTestResult>(`/providers/keys/${keyId}/test`);
  return data;
}

export async function revokeProviderKey(keyId: string) {
  const { data } = await api.post<import('../types/api').ProviderKey>(`/providers/keys/${keyId}/revoke`, {});
  return data;
}

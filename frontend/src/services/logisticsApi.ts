import { api } from './api';
import type {
  Alert,
  ForecastResponse,
  InventoryOverviewRow,
  ReplenishmentPlan,
  RouteOptimizePayload,
  RouteOptimizeResponse,
  RouteScheduleSummary,
  Shipment,
  ShipmentStatus,
} from '../types/api';

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

export async function uploadInventoryCsv(file: File) {
  const formData = new FormData();
  formData.append('file', file);
  const { data } = await api.post('/ingestion/inventory-csv', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return data;
}

export async function uploadOrdersCsv(file: File) {
  const formData = new FormData();
  formData.append('file', file);
  const { data } = await api.post('/ingestion/orders-csv', formData, {
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

import { api } from './api';
import type {
  CashCloseSummary,
  Customer,
  DeliveryOrder,
  DispatchRun,
  Driver,
  DriverLink,
  DriverManifest,
  DispatchStop,
  FleetDispatchPlanResponse,
  CustomerTrackingLink,
  CustomerTrackingView,
} from '../types/api';

export async function listCustomers(): Promise<Customer[]> {
  const { data } = await api.get<Customer[]>('/dispatch/customers');
  return data;
}

export async function createCustomer(payload: {
  code: string;
  name: string;
  phone?: string;
  address: string;
  latitude: number;
  longitude: number;
}): Promise<Customer> {
  const { data } = await api.post<Customer>('/dispatch/customers', payload);
  return data;
}

export async function listDeliveryOrders(): Promise<DeliveryOrder[]> {
  const { data } = await api.get<DeliveryOrder[]>('/dispatch/orders');
  return data;
}

export async function createDeliveryOrder(payload: {
  order_no: string;
  customer_id: string;
  quantity_units: number;
  cod_amount_etb: number;
  window_start?: string;
  window_end?: string;
  service_minutes?: number;
  priority?: number;
  notes?: string;
}): Promise<DeliveryOrder> {
  const { data } = await api.post<DeliveryOrder>('/dispatch/orders', payload);
  return data;
}

export async function listDrivers(): Promise<Driver[]> {
  const { data } = await api.get<Driver[]>('/drivers');
  return data;
}

export async function createDriver(payload: {
  full_name: string;
  phone: string;
  vehicle_plate?: string;
}): Promise<Driver> {
  const { data } = await api.post<Driver>('/drivers', payload);
  return data;
}

export async function planDispatchRun(payload: {
  route_name: string;
  plan_date: string;
  start_label: string;
  start_latitude: number;
  start_longitude: number;
  order_ids: string[];
  driver_id?: string;
  vehicle_capacity_units: number;
  max_stops: number;
  average_speed_kmh: number;
}): Promise<DispatchRun> {
  const { data } = await api.post<DispatchRun>('/dispatch/runs', payload);
  return data;
}

export async function planFleetDispatch(payload: {
  route_name: string;
  plan_date: string;
  start_label: string;
  start_latitude: number;
  start_longitude: number;
  order_ids: string[];
  vehicles: {
    driver_id: string;
    vehicle_capacity_units: number;
    max_stops: number;
    average_speed_kmh: number;
  }[];
}): Promise<FleetDispatchPlanResponse> {
  const { data } = await api.post<FleetDispatchPlanResponse>(
    '/dispatch/plan-fleet',
    payload,
  );
  return data;
}

export async function listDispatchRuns(): Promise<DispatchRun[]> {
  const { data } = await api.get<DispatchRun[]>('/dispatch/runs');
  return data;
}

export async function getDispatchRun(runId: string): Promise<DispatchRun> {
  const { data } = await api.get<DispatchRun>(`/dispatch/runs/${runId}`);
  return data;
}

export async function createDriverLink(runId: string): Promise<DriverLink> {
  const { data } = await api.post<DriverLink>(`/dispatch/runs/${runId}/driver-link`);
  return data;
}

export async function createCustomerTrackingLink(
  orderId: string,
): Promise<CustomerTrackingLink> {
  const { data } = await api.post<CustomerTrackingLink>(
    `/dispatch/orders/${orderId}/tracking-link`,
  );
  return data;
}

export async function closeDispatchCash(
  runId: string,
  payload?: {
    handed_over_etb?: number | string;
    deposit_bank?: 'cbe' | 'dashen';
    deposit_reference?: string;
    note?: string;
  },
): Promise<CashCloseSummary> {
  const { data } = await api.post<CashCloseSummary>(
    `/dispatch/runs/${runId}/close-cash`,
    payload,
  );
  return data;
}

export async function getProofBlob(orderId: string, proofId: string): Promise<Blob> {
  const { data } = await api.get<Blob>(
    `/dispatch/orders/${orderId}/proofs/${proofId}/file`,
    { responseType: 'blob' },
  );
  return data;
}

const driverBaseUrl = import.meta.env.VITE_API_BASE_URL || '/api/v1';

export class DriverRequestError extends Error {
  status: number;

  constructor(status: number, message: string) {
    super(message);
    this.name = 'DriverRequestError';
    this.status = status;
  }
}

async function driverRequest<T>(
  token: string,
  path: string,
  init?: RequestInit,
): Promise<T> {
  const response = await fetch(`${driverBaseUrl}${path}`, {
    ...init,
    headers: {
      ...(init?.headers || {}),
      'X-Driver-Token': token,
    },
  });
  if (!response.ok) {
    let detail = `Request failed (${response.status})`;
    try {
      const body = (await response.json()) as { detail?: string };
      detail = body.detail || detail;
    } catch {
      // keep the status-based detail
    }
    throw new DriverRequestError(response.status, detail);
  }
  if (response.status === 204) return undefined as T;
  return (await response.json()) as T;
}

export async function getDriverManifest(token: string): Promise<DriverManifest> {
  return driverRequest<DriverManifest>(token, '/dispatch/driver/manifest');
}

export async function getCustomerTracking(token: string): Promise<CustomerTrackingView> {
  const response = await fetch(`${driverBaseUrl}/dispatch/tracking`, {
    headers: { 'X-Tracking-Token': token },
  });
  if (!response.ok) {
    let detail = `Tracking request failed (${response.status})`;
    try {
      const body = (await response.json()) as { detail?: string };
      detail = body.detail || detail;
    } catch {
      // keep the status-based detail
    }
    throw new Error(detail);
  }
  return (await response.json()) as CustomerTrackingView;
}

export async function updateDriverOrderStatus(
  token: string,
  orderId: string,
  status: 'in_transit' | 'delivered' | 'failed',
  note?: string,
): Promise<DispatchStop> {
  return driverRequest<DispatchStop>(token, `/dispatch/driver/orders/${orderId}/status`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ status, note }),
  });
}

export async function declareDriverCash(
  token: string,
  orderId: string,
  collectedEtb: number,
  note?: string,
): Promise<DispatchStop> {
  return driverRequest<DispatchStop>(token, `/dispatch/driver/orders/${orderId}/cash`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ collected_etb: collectedEtb, note }),
  });
}

export async function uploadDriverProof(
  token: string,
  orderId: string,
  file: Blob,
  fileName?: string,
  recipientName?: string,
  notes?: string,
): Promise<{ id: string }> {
  const form = new FormData();
  const resolvedName =
    fileName || (typeof File !== 'undefined' && file instanceof File ? file.name : 'proof.jpg');
  form.append('file', file, resolvedName);
  if (recipientName) form.append('recipient_name', recipientName);
  if (notes) form.append('notes', notes);
  return driverRequest<{ id: string }>(token, `/dispatch/driver/orders/${orderId}/proof`, {
    method: 'POST',
    body: form,
  });
}

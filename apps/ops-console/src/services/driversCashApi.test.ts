import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { api } from './api';
import {
  createDriver,
  createShipment,
  deactivateDriver,
  declareCash,
  getCashLedger,
  listCashCollections,
  listDriverShipments,
  listDrivers,
  settleCash,
  updateDriver,
  updateShipmentStatus,
} from './logisticsApi';

/**
 * Contract pin for the console side of the driver roster and cash-on-delivery
 * ledger (NB-86). Every assertion here is about the *wire* — method, path, and
 * payload — because that is the seam where a console/API disagreement would
 * silently break the operator's end-of-day cash position.
 */

type CapturedConfig = {
  method?: string;
  url?: string;
  data?: unknown;
  params?: unknown;
};

let captured: CapturedConfig = {};

const noopStorage = {
  getItem: () => null,
  setItem: () => undefined,
  removeItem: () => undefined,
  clear: () => undefined,
};

function stubAdapter(payload: unknown) {
  api.defaults.adapter = async (config) => {
    captured = config as unknown as CapturedConfig;
    return { data: payload, status: 200, statusText: 'OK', headers: {}, config };
  };
}

/** axios serialises `data` before the adapter sees it; normalise either shape. */
function sentBody(): Record<string, unknown> {
  if (typeof captured.data === 'string') {
    return JSON.parse(captured.data) as Record<string, unknown>;
  }
  return (captured.data ?? {}) as Record<string, unknown>;
}

beforeEach(() => {
  vi.stubGlobal('sessionStorage', noopStorage);
  vi.stubGlobal('localStorage', noopStorage);
  captured = {};
  stubAdapter([]);
});

afterEach(() => {
  vi.unstubAllGlobals();
  delete api.defaults.adapter;
});

describe('driver roster client (NB-86)', () => {
  it('lists the roster without a status filter by default', async () => {
    await listDrivers();
    expect(captured.method).toBe('get');
    expect(captured.url).toBe('/drivers');
    expect(captured.params).toBeUndefined();
  });

  it('passes the status filter through as a query param', async () => {
    await listDrivers('active');
    expect(captured.method).toBe('get');
    expect(captured.url).toBe('/drivers');
    expect(captured.params).toEqual({ status: 'active' });
  });

  it('creates a driver with the phone the operator actually identifies them by', async () => {
    await createDriver({ full_name: 'Yohannes Tesfaye', phone: '+251911000001' });
    expect(captured.method).toBe('post');
    expect(captured.url).toBe('/drivers');
    expect(sentBody()).toEqual({ full_name: 'Yohannes Tesfaye', phone: '+251911000001' });
  });

  it('updates a driver by id with PATCH', async () => {
    await updateDriver('drv-1', { vehicle_plate: 'AA-3-B12345' });
    expect(captured.method).toBe('patch');
    expect(captured.url).toBe('/drivers/drv-1');
    expect(sentBody()).toEqual({ vehicle_plate: 'AA-3-B12345' });
  });

  it('deactivates via DELETE rather than removing delivery history', async () => {
    await deactivateDriver('drv-1');
    expect(captured.method).toBe('delete');
    expect(captured.url).toBe('/drivers/drv-1');
  });

  it('answers "what is on the van" from the driver-scoped shipment endpoint', async () => {
    await listDriverShipments('drv-1');
    expect(captured.method).toBe('get');
    expect(captured.url).toBe('/drivers/drv-1/shipments');
  });
});

describe('cash-on-delivery ledger client (NB-86)', () => {
  it('reads the end-of-day ledger', async () => {
    await getCashLedger();
    expect(captured.method).toBe('get');
    expect(captured.url).toBe('/cash-collections/ledger');
  });

  it('lists cash records, forwarding filters', async () => {
    await listCashCollections({ status: 'outstanding', driver_id: 'drv-1' });
    expect(captured.method).toBe('get');
    expect(captured.url).toBe('/cash-collections');
    expect(captured.params).toEqual({ status: 'outstanding', driver_id: 'drv-1' });
  });

  it('declares cash the driver is holding', async () => {
    await declareCash('cash-1', { collected_etb: 2000, note: 'Paid part in cash' });
    expect(captured.method).toBe('post');
    expect(captured.url).toBe('/cash-collections/cash-1/declare');
    expect(sentBody()).toEqual({ collected_etb: 2000, note: 'Paid part in cash' });
  });

  it('settles a record through the admin-only office close', async () => {
    await settleCash('cash-1', { note: 'Banked Monday' });
    expect(captured.method).toBe('post');
    expect(captured.url).toBe('/cash-collections/cash-1/settle');
    expect(sentBody()).toEqual({ note: 'Banked Monday' });
  });

  it('settles with an empty body when no note is supplied', async () => {
    await settleCash('cash-1');
    expect(captured.url).toBe('/cash-collections/cash-1/settle');
    expect(sentBody()).toEqual({});
  });
});

describe('shipment cash integration (NB-86)', () => {
  it('carries driver and cash-on-delivery on create', async () => {
    await createShipment({
      shipment_no: 'SHP-1',
      origin_warehouse_code: 'WH-001',
      destination_warehouse_code: 'WH-002',
      sku: 'SKU-001',
      quantity_units: 10,
      driver_id: 'drv-1',
      cod_amount_etb: 2500,
    });
    expect(captured.method).toBe('post');
    expect(captured.url).toBe('/shipments');
    expect(sentBody()).toMatchObject({ driver_id: 'drv-1', cod_amount_etb: 2500 });
  });

  it('sends the delivery confirmation and its cash figure in one call', async () => {
    await updateShipmentStatus('shp-1', {
      status: 'delivered',
      cash_collected_etb: 2000,
      cash_note: 'Customer paid part in cash',
    });
    expect(captured.method).toBe('post');
    expect(captured.url).toBe('/shipments/shp-1/status');
    expect(sentBody()).toEqual({
      status: 'delivered',
      cash_collected_etb: 2000,
      cash_note: 'Customer paid part in cash',
    });
  });

  it('omits the cash figure entirely for a non-cash delivery', async () => {
    // The API rejects cash_collected_etb on any status other than delivered,
    // and omits it here because a no-COD shipment has no cash to declare.
    await updateShipmentStatus('shp-1', { status: 'delivered', cash_collected_etb: undefined });
    expect(sentBody()).toEqual({ status: 'delivered' });
    expect(sentBody()).not.toHaveProperty('cash_collected_etb');
  });
});

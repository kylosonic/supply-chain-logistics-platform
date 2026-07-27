import { FormEvent, useEffect, useState } from 'react';

import { createShipment, listShipments, updateShipmentStatus } from '../services/logisticsApi';
import type { Shipment, ShipmentStatus } from '../types/api';

const statusTransitions: ShipmentStatus[] = ['in_transit', 'delayed', 'delivered', 'cancelled'];

export function ShipmentsPage() {
  const [shipments, setShipments] = useState<Shipment[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [creating, setCreating] = useState(false);
  const [form, setForm] = useState({
    shipment_no: '',
    origin_warehouse_code: '',
    destination_warehouse_code: '',
    sku: '',
    quantity_units: 1,
  });

  async function loadShipments() {
    try {
      setError(null);
      const rows = await listShipments();
      setShipments(rows);
    } catch (err: any) {
      setError(err?.response?.data?.detail || err?.message || 'Failed to load shipments');
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadShipments();
  }, []);

  async function onCreate(event: FormEvent) {
    event.preventDefault();
    try {
      setCreating(true);
      setError(null);
      await createShipment(form);
      setForm({
        shipment_no: '',
        origin_warehouse_code: '',
        destination_warehouse_code: '',
        sku: '',
        quantity_units: 1,
      });
      await loadShipments();
    } catch (err: any) {
      setError(err?.response?.data?.detail || err?.message || 'Failed to create shipment');
    } finally {
      setCreating(false);
    }
  }

  async function onStatusUpdate(shipment: Shipment, status: ShipmentStatus) {
    const payload: { status: ShipmentStatus; delay_reason?: string } = { status };
    if (status === 'delayed') {
      const reason = window.prompt('Provide delay reason', shipment.delay_reason || 'Traffic delay');
      if (!reason) return;
      payload.delay_reason = reason;
    }
    try {
      setError(null);
      await updateShipmentStatus(shipment.id, payload);
      await loadShipments();
    } catch (err: any) {
      setError(err?.response?.data?.detail || err?.message || 'Failed to update shipment status');
    }
  }

  return (
    <div className="space-y-6">
      <div className="rounded-lg border border-slate-200 bg-white p-4">
        <h2 className="mb-3 text-sm font-semibold text-slate-700">Create Shipment</h2>
        <form className="grid grid-cols-1 gap-3 md:grid-cols-5" onSubmit={onCreate}>
          <input
            className="rounded border border-slate-300 px-3 py-2 text-sm"
            placeholder="Shipment No"
            value={form.shipment_no}
            onChange={(e) => setForm((prev) => ({ ...prev, shipment_no: e.target.value }))}
            required
          />
          <input
            className="rounded border border-slate-300 px-3 py-2 text-sm"
            placeholder="Origin Code"
            value={form.origin_warehouse_code}
            onChange={(e) => setForm((prev) => ({ ...prev, origin_warehouse_code: e.target.value.toUpperCase() }))}
            required
          />
          <input
            className="rounded border border-slate-300 px-3 py-2 text-sm"
            placeholder="Destination Code"
            value={form.destination_warehouse_code}
            onChange={(e) => setForm((prev) => ({ ...prev, destination_warehouse_code: e.target.value.toUpperCase() }))}
            required
          />
          <input
            className="rounded border border-slate-300 px-3 py-2 text-sm"
            placeholder="SKU"
            value={form.sku}
            onChange={(e) => setForm((prev) => ({ ...prev, sku: e.target.value.toUpperCase() }))}
            required
          />
          <div className="flex gap-2">
            <input
              className="w-24 rounded border border-slate-300 px-3 py-2 text-sm"
              type="number"
              min={1}
              value={form.quantity_units}
              onChange={(e) => setForm((prev) => ({ ...prev, quantity_units: Number(e.target.value) }))}
              required
            />
            <button
              type="submit"
              disabled={creating}
              className="rounded bg-slate-900 px-3 py-2 text-xs font-medium text-white disabled:opacity-60"
            >
              {creating ? 'Creating...' : 'Create'}
            </button>
          </div>
        </form>
      </div>

      {error ? <p className="text-sm text-red-600">{error}</p> : null}
      {loading ? <p className="text-slate-600">Loading shipments...</p> : null}

      <div className="overflow-x-auto rounded-lg border border-slate-200 bg-white">
        <table className="min-w-full divide-y divide-slate-200 text-sm">
          <thead className="bg-slate-50">
            <tr>
              <th className="px-3 py-2 text-left">Shipment</th>
              <th className="px-3 py-2 text-left">Lane</th>
              <th className="px-3 py-2 text-left">SKU</th>
              <th className="px-3 py-2 text-left">Qty</th>
              <th className="px-3 py-2 text-left">Status</th>
              <th className="px-3 py-2 text-left">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {shipments.map((shipment) => (
              <tr key={shipment.id}>
                <td className="px-3 py-2">
                  <div className="font-medium text-slate-800">{shipment.shipment_no}</div>
                  <div className="text-xs text-slate-500">{new Date(shipment.created_at).toLocaleString()}</div>
                </td>
                <td className="px-3 py-2">{shipment.origin_warehouse_code} → {shipment.destination_warehouse_code}</td>
                <td className="px-3 py-2">{shipment.sku}</td>
                <td className="px-3 py-2">{shipment.quantity_units}</td>
                <td className="px-3 py-2">{shipment.status}</td>
                <td className="px-3 py-2">
                  <div className="flex flex-wrap gap-2">
                    {statusTransitions.map((status) => (
                      <button
                        key={status}
                        className="rounded border border-slate-300 px-2 py-1 text-xs hover:bg-slate-100"
                        onClick={() => onStatusUpdate(shipment, status)}
                        disabled={shipment.status === status}
                      >
                        Mark {status}
                      </button>
                    ))}
                  </div>
                </td>
              </tr>
            ))}
            {shipments.length === 0 ? (
              <tr>
                <td colSpan={6} className="px-3 py-6 text-center text-slate-500">
                  No shipments yet.
                </td>
              </tr>
            ) : null}
          </tbody>
        </table>
      </div>
    </div>
  );
}

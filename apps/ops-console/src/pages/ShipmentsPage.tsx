import { FormEvent, useEffect, useState } from 'react';

import { MetricTile } from '../components/ui/MetricTile';
import { PageHeader } from '../components/ui/PageHeader';
import { Panel } from '../components/ui/Panel';
import { StatusBadge } from '../components/ui/StatusBadge';
import { createShipment, listShipments, updateShipmentStatus } from '../services/logisticsApi';
import type { Shipment, ShipmentStatus } from '../types/api';

const statusTransitions: ShipmentStatus[] = ['in_transit', 'delayed', 'delivered', 'cancelled'];

function statusTone(status: ShipmentStatus) {
  if (status === 'delivered') return 'success';
  if (status === 'delayed' || status === 'cancelled') return 'danger';
  if (status === 'in_transit') return 'warning';
  return 'neutral';
}

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

  const counts = {
    planned: shipments.filter((shipment) => shipment.status === 'planned').length,
    inTransit: shipments.filter((shipment) => shipment.status === 'in_transit').length,
    delayed: shipments.filter((shipment) => shipment.status === 'delayed').length,
    delivered: shipments.filter((shipment) => shipment.status === 'delivered').length,
  };

  const fieldClassName =
    'min-h-12 rounded-2xl border border-slate-700 bg-slate-900/80 px-4 text-sm text-slate-100 outline-none transition focus:border-sky-400/50';

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Shipment board"
        title="Track movement health across every lane"
        description="Create shipments, monitor lane progression, and update status without losing the context around delay pressure and throughput."
      />

      <div className="grid grid-cols-1 gap-4 xl:grid-cols-4">
        <MetricTile title="Planned" value={counts.planned} detail="Shipments queued but not yet in motion." tone="neutral" />
        <MetricTile title="In transit" value={counts.inTransit} detail="Active movement currently underway across tracked lanes." tone="info" />
        <MetricTile title="Delayed" value={counts.delayed} detail="Shipments requiring intervention or follow-up." tone={counts.delayed > 0 ? 'danger' : 'success'} />
        <MetricTile title="Delivered" value={counts.delivered} detail="Completed movements recorded in the current board." tone="success" />
      </div>

      <Panel
        eyebrow="Manual entry"
        title="Create a shipment"
        description="Use this for direct movement creation when the order flow does not originate from a bulk CSV load."
      >
        <form className="grid grid-cols-1 gap-3 lg:grid-cols-5" onSubmit={onCreate}>
          <input className={fieldClassName} placeholder="Shipment No" value={form.shipment_no} onChange={(e) => setForm((prev) => ({ ...prev, shipment_no: e.target.value }))} required />
          <input className={fieldClassName} placeholder="Origin Code" value={form.origin_warehouse_code} onChange={(e) => setForm((prev) => ({ ...prev, origin_warehouse_code: e.target.value.toUpperCase() }))} required />
          <input className={fieldClassName} placeholder="Destination Code" value={form.destination_warehouse_code} onChange={(e) => setForm((prev) => ({ ...prev, destination_warehouse_code: e.target.value.toUpperCase() }))} required />
          <input className={fieldClassName} placeholder="SKU" value={form.sku} onChange={(e) => setForm((prev) => ({ ...prev, sku: e.target.value.toUpperCase() }))} required />
          <div className="flex gap-2">
            <input className={`${fieldClassName} w-full`} type="number" min={1} value={form.quantity_units} onChange={(e) => setForm((prev) => ({ ...prev, quantity_units: Number(e.target.value) }))} required />
            <button
              type="submit"
              disabled={creating}
              className="inline-flex min-h-12 items-center justify-center rounded-full bg-gradient-to-r from-sky-300 via-sky-400 to-teal-300 px-5 text-sm font-semibold text-slate-950 transition hover:brightness-105 disabled:cursor-not-allowed disabled:opacity-60"
            >
              {creating ? 'Creating...' : 'Create'}
            </button>
          </div>
        </form>
      </Panel>

      <Panel
        eyebrow="Movement board"
        title="Shipment lifecycle"
        description="Keep each lane visible and progress status deliberately when a movement changes state."
      >
        {error ? <p className="text-sm text-rose-300">{error}</p> : null}
        {loading ? <p className="text-sm text-slate-400">Loading shipments...</p> : null}

        <div className="space-y-3">
          {shipments.map((shipment) => (
            <article key={shipment.id} className="rounded-[22px] border border-slate-800 bg-slate-900/70 p-4">
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div>
                  <div className="flex flex-wrap items-center gap-2">
                    <StatusBadge label={shipment.status} tone={statusTone(shipment.status)} />
                    <span className="text-xs uppercase tracking-[0.18em] text-slate-500">{new Date(shipment.created_at).toLocaleString()}</span>
                  </div>
                  <h3 className="mt-2 font-['Space_Grotesk'] text-lg font-semibold text-slate-50">{shipment.shipment_no}</h3>
                </div>
                <div className="text-right text-sm text-slate-400">
                  <p>{shipment.origin_warehouse_code} to {shipment.destination_warehouse_code}</p>
                  <p>{shipment.sku} - {shipment.quantity_units} units</p>
                </div>
              </div>

              <p className="mt-3 text-sm leading-6 text-slate-400">
                {shipment.delay_reason ? `Delay note: ${shipment.delay_reason}` : 'No delay reason logged for this shipment.'}
              </p>

              <div className="mt-4 flex flex-wrap gap-2">
                {statusTransitions.map((status) => (
                  <button
                    key={status}
                    className="rounded-full border border-slate-700 px-3 py-2 text-xs font-semibold text-slate-200 transition hover:border-slate-500 hover:bg-slate-950 disabled:cursor-not-allowed disabled:opacity-50"
                    onClick={() => onStatusUpdate(shipment, status)}
                    disabled={shipment.status === status}
                  >
                    Mark {status}
                  </button>
                ))}
              </div>
            </article>
          ))}

          {!loading && shipments.length === 0 ? <p className="text-sm text-slate-500">No shipments yet.</p> : null}
        </div>
      </Panel>
    </div>
  );
}

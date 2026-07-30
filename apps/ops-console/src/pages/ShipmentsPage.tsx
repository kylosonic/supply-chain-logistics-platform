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

/* ── Inline delay reason dialog ─────────────────────────────── */

function DelayReasonDialog({
  shipmentNo,
  defaultReason,
  onConfirm,
  onCancel,
}: {
  shipmentNo: string;
  defaultReason: string;
  onConfirm: (reason: string) => void;
  onCancel: () => void;
}) {
  const [reason, setReason] = useState(defaultReason);

  return (
    <div className="animate-fade-in fixed inset-0 z-50 grid place-items-center bg-slate-950/70 backdrop-blur-sm">
      <div className="animate-scale-in w-full max-w-lg rounded-[28px] border border-slate-800/80 bg-slate-950 p-6 shadow-[0_32px_100px_rgba(2,12,20,0.6)]">
        <p className="text-xs font-semibold uppercase tracking-[0.24em] text-sky-300/80">Delay reason</p>
        <h3 className="mt-2 font-['Space_Grotesk'] text-xl font-semibold text-slate-50">
          Mark {shipmentNo} as delayed
        </h3>
        <p className="mt-2 text-sm text-slate-400">Provide a reason for the delay so the team can track root causes and take corrective action.</p>
        <textarea
          autoFocus
          className="mt-4 min-h-24 w-full rounded-2xl border border-slate-700 bg-slate-900/80 px-4 py-3 text-sm text-slate-100 outline-none transition focus:border-sky-400/50"
          placeholder="Describe the delay reason..."
          value={reason}
          onChange={(e) => setReason(e.target.value)}
        />
        <div className="mt-4 flex justify-end gap-2">
          <button
            type="button"
            onClick={onCancel}
            className="glow-ring inline-flex min-h-10 items-center justify-center rounded-full border border-slate-700 px-4 text-sm font-semibold text-slate-200 transition hover:border-slate-500 hover:bg-slate-900"
          >
            Cancel
          </button>
          <button
            type="button"
            onClick={() => onConfirm(reason)}
            disabled={!reason.trim()}
            className="glow-ring inline-flex min-h-10 items-center justify-center rounded-full bg-gradient-to-r from-sky-300 via-sky-400 to-teal-300 px-5 text-sm font-semibold text-slate-950 transition hover:brightness-105 disabled:cursor-not-allowed disabled:opacity-60"
          >
            Confirm delay
          </button>
        </div>
      </div>
    </div>
  );
}

function SkeletonBlock({ className }: { className?: string }) {
  return <div className={`skeleton ${className ?? ''}`} />;
}

export function ShipmentsPage() {
  const [shipments, setShipments] = useState<Shipment[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [creating, setCreating] = useState(false);
  const [delayDialog, setDelayDialog] = useState<{ shipment: Shipment } | null>(null);
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
    if (status === 'delayed') {
      setDelayDialog({ shipment });
      return;
    }
    const payload: { status: ShipmentStatus; delay_reason?: string } = { status };
    try {
      setError(null);
      await updateShipmentStatus(shipment.id, payload);
      await loadShipments();
    } catch (err: any) {
      setError(err?.response?.data?.detail || err?.message || 'Failed to update shipment status');
    }
  }

  async function onDelayConfirm(reason: string) {
    if (!delayDialog) return;
    try {
      setError(null);
      await updateShipmentStatus(delayDialog.shipment.id, { status: 'delayed', delay_reason: reason });
      await loadShipments();
    } catch (err: any) {
      setError(err?.response?.data?.detail || err?.message || 'Failed to update shipment status');
    } finally {
      setDelayDialog(null);
    }
  }

  const counts = {
    planned: shipments.filter((shipment) => shipment.status === 'planned').length,
    inTransit: shipments.filter((shipment) => shipment.status === 'in_transit').length,
    delayed: shipments.filter((shipment) => shipment.status === 'delayed').length,
    delivered: shipments.filter((shipment) => shipment.status === 'delivered').length,
  };

  const fieldClassName =
    'glow-ring min-h-12 rounded-2xl border border-slate-700 bg-slate-900/80 px-4 text-sm text-slate-100 outline-none transition focus:border-sky-400/50';

  return (
    <div className="space-y-6">
      {delayDialog ? (
        <DelayReasonDialog
          shipmentNo={delayDialog.shipment.shipment_no}
          defaultReason={delayDialog.shipment.delay_reason || 'Traffic delay'}
          onConfirm={onDelayConfirm}
          onCancel={() => setDelayDialog(null)}
        />
      ) : null}

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
              className="glow-ring inline-flex min-h-12 items-center justify-center gap-2 rounded-full bg-gradient-to-r from-sky-300 via-sky-400 to-teal-300 px-5 text-sm font-semibold text-slate-950 transition hover:brightness-105 disabled:cursor-not-allowed disabled:opacity-60"
            >
              {creating ? (
                <svg className="animate-spin-slow h-4 w-4" viewBox="0 0 24 24" fill="none"><circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeDasharray="50 20" /></svg>
              ) : null}
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
        {loading ? (
          <div className="space-y-3">
            {[1, 2, 3].map((i) => (
              <SkeletonBlock key={i} className="h-[120px] rounded-[22px]" />
            ))}
          </div>
        ) : null}

        <div className="space-y-3">
          {shipments.map((shipment, index) => (
            <article key={shipment.id} className="animate-fade-in hover-lift rounded-[22px] border border-slate-800 bg-slate-900/70 p-4" style={{ animationDelay: `${index * 0.04}s` }}>
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div>
                  <div className="flex flex-wrap items-center gap-2">
                    <StatusBadge label={shipment.status} tone={statusTone(shipment.status)} />
                    <span className="text-xs uppercase tracking-[0.18em] text-slate-500">{new Date(shipment.created_at).toLocaleString()}</span>
                  </div>
                  <h3 className="mt-2 font-['Space_Grotesk'] text-lg font-semibold text-slate-50">{shipment.shipment_no}</h3>
                </div>
                <div className="text-right text-sm text-slate-400">
                  <p>{shipment.origin_warehouse_code} → {shipment.destination_warehouse_code}</p>
                  <p>{shipment.sku} · {shipment.quantity_units} units</p>
                </div>
              </div>

              <p className="mt-3 text-sm leading-6 text-slate-400">
                {shipment.delay_reason ? `Delay note: ${shipment.delay_reason}` : 'No delay reason logged for this shipment.'}
              </p>

              <div className="mt-4 flex flex-wrap gap-2">
                {statusTransitions.map((status) => (
                  <button
                    key={status}
                    className="glow-ring rounded-full border border-slate-700 px-3 py-2 text-xs font-semibold text-slate-200 transition hover:border-slate-500 hover:bg-slate-950 disabled:cursor-not-allowed disabled:opacity-50"
                    onClick={() => onStatusUpdate(shipment, status)}
                    disabled={shipment.status === status}
                  >
                    Mark {status.replace('_', ' ')}
                  </button>
                ))}
              </div>
            </article>
          ))}

          {!loading && shipments.length === 0 ? (
            <div className="animate-fade-in rounded-[22px] border border-slate-800 bg-slate-900/40 p-6 text-center">
              <p className="font-['Space_Grotesk'] text-lg font-semibold text-slate-300">No shipments yet</p>
              <p className="mt-1 text-sm text-slate-500">Create your first shipment using the form above.</p>
            </div>
          ) : null}
        </div>
      </Panel>
    </div>
  );
}

import { FormEvent, useEffect, useState } from 'react';

import { Dialog } from '../components/ui/Dialog';
import { MetricTile } from '../components/ui/MetricTile';
import { PageHeader } from '../components/ui/PageHeader';
import { Panel } from '../components/ui/Panel';
import { StatusBadge } from '../components/ui/StatusBadge';
import { createShipment, listDrivers, listShipments, updateShipmentStatus } from '../services/logisticsApi';
import type { Driver, Shipment, ShipmentStatus } from '../types/api';
import { apiErrorMessage } from '../services/authErrors';

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
    <Dialog
      eyebrow="Delay reason"
      title={`Mark ${shipmentNo} as delayed`}
      description="Provide a reason for the delay so the team can track root causes and take corrective action."
      actions={
        <>
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
            className="glow-ring inline-flex min-h-10 items-center justify-center rounded-lg bg-sky-500 px-5 text-sm font-semibold text-slate-950 transition-colors hover:bg-sky-400 disabled:cursor-not-allowed disabled:opacity-60"
          >
            Confirm delay
          </button>
        </>
      }
    >
      <textarea
        autoFocus
        className="fp-input min-h-24 px-4 py-3"
        placeholder="Describe the delay reason..."
        value={reason}
        onChange={(e) => setReason(e.target.value)}
      />
    </Dialog>
  );
}

function SkeletonBlock({ className }: { className?: string }) {
  return <div className={`skeleton ${className ?? ''}`} />;
}

/**
 * NB-86: the delivery confirmation and its cash figure are captured together,
 * because a driver who never makes a second call must still produce a complete
 * cash record. A non-COD shipment records the delivery only.
 */
function DeliveryCashDialog({
  shipment,
  onConfirm,
  onCancel,
}: {
  shipment: Shipment;
  onConfirm: (cashCollected: number | undefined, note: string) => void;
  onCancel: () => void;
}) {
  const expected = Number(shipment.cod_amount_etb ?? 0);
  const hasCod = expected > 0;
  const [collected, setCollected] = useState(String(shipment.cod_amount_etb ?? '0'));
  const [note, setNote] = useState('');

  const entered = Number(collected);
  const shortfall = Number.isFinite(entered) ? Math.max(0, expected - entered) : 0;

  return (
    <Dialog
      eyebrow="Delivery confirmation"
      title={`Deliver ${shipment.shipment_no}`}
      description={
        hasCod
          ? `Cash on delivery of ${expected.toFixed(2)} ETB is expected at the door. Enter what the driver actually collected — a shortfall is recorded, not hidden.`
          : 'This shipment carries no cash on delivery, so confirming records the delivery only.'
      }
      actions={
        <>
          <button
            type="button"
            onClick={onCancel}
            className="glow-ring inline-flex min-h-10 items-center justify-center rounded-full border border-slate-700 px-4 text-sm font-semibold text-slate-200 transition hover:border-slate-500 hover:bg-slate-900"
          >
            Cancel
          </button>
          <button
            type="button"
            onClick={() => onConfirm(hasCod ? entered : undefined, note)}
            disabled={hasCod && (!Number.isFinite(entered) || entered < 0)}
            className="glow-ring inline-flex min-h-10 items-center justify-center rounded-lg bg-sky-500 px-5 text-sm font-semibold text-slate-950 transition-colors hover:bg-sky-400 disabled:cursor-not-allowed disabled:opacity-60"
          >
            Confirm delivery
          </button>
        </>
      }
    >
      <div className="grid gap-4">
        {hasCod ? (
          <>
            <label className="grid gap-2 text-sm text-slate-300">
              Cash collected (ETB)
              <input
                autoFocus
                className="fp-input"
                type="number"
                min={0}
                step="0.01"
                value={collected}
                onChange={(e) => setCollected(e.target.value)}
              />
            </label>
            <p className={`text-sm ${shortfall > 0 ? 'text-amber-300' : 'text-slate-400'}`}>
              {shortfall > 0
                ? `Shortfall of ${shortfall.toFixed(2)} ETB will be recorded against this delivery.`
                : 'This clears the expected amount in full.'}
            </p>
          </>
        ) : null}
        <label className="grid gap-2 text-sm text-slate-300">
          Delivery note (optional)
          <textarea
            className="fp-input min-h-20 px-4 py-3"
            placeholder="Anything the office should know about this delivery..."
            value={note}
            onChange={(e) => setNote(e.target.value)}
          />
        </label>
      </div>
    </Dialog>
  );
}

export function ShipmentsPage() {
  const [shipments, setShipments] = useState<Shipment[]>([]);
  const [drivers, setDrivers] = useState<Driver[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [creating, setCreating] = useState(false);
  const [delayDialog, setDelayDialog] = useState<{ shipment: Shipment } | null>(null);
  const [deliveryDialog, setDeliveryDialog] = useState<{ shipment: Shipment } | null>(null);
  const [form, setForm] = useState({
    shipment_no: '',
    origin_warehouse_code: '',
    destination_warehouse_code: '',
    sku: '',
    quantity_units: 1,
    driver_id: '',
    cod_amount_etb: 0,
  });

  async function loadShipments() {
    try {
      setError(null);
      const rows = await listShipments();
      setShipments(rows);
    } catch (err) {
      setError(apiErrorMessage(err, 'Failed to load shipments'));
    } finally {
      setLoading(false);
    }
  }

  async function loadDrivers() {
    try {
      setDrivers(await listDrivers('active'));
    } catch {
      // The roster only feeds the assignment picker; a failure here must not
      // blank the shipment board.
      setDrivers([]);
    }
  }

  useEffect(() => {
    loadShipments();
    loadDrivers();
  }, []);

  async function onCreate(event: FormEvent) {
    event.preventDefault();
    try {
      setCreating(true);
      setError(null);
      await createShipment({
        shipment_no: form.shipment_no,
        origin_warehouse_code: form.origin_warehouse_code,
        destination_warehouse_code: form.destination_warehouse_code,
        sku: form.sku,
        quantity_units: form.quantity_units,
        driver_id: form.driver_id || null,
        cod_amount_etb: form.cod_amount_etb,
      });
      setForm({
        shipment_no: '',
        origin_warehouse_code: '',
        destination_warehouse_code: '',
        sku: '',
        quantity_units: 1,
        driver_id: '',
        cod_amount_etb: 0,
      });
      await loadShipments();
    } catch (err) {
      setError(apiErrorMessage(err, 'Failed to create shipment'));
    } finally {
      setCreating(false);
    }
  }

  async function onStatusUpdate(shipment: Shipment, status: ShipmentStatus) {
    if (status === 'delayed') {
      setDelayDialog({ shipment });
      return;
    }
    if (status === 'delivered') {
      setDeliveryDialog({ shipment });
      return;
    }
    const payload: { status: ShipmentStatus; delay_reason?: string } = { status };
    try {
      setError(null);
      await updateShipmentStatus(shipment.id, payload);
      await loadShipments();
    } catch (err) {
      setError(apiErrorMessage(err, 'Failed to update shipment status'));
    }
  }

  async function onDeliveryConfirm(cashCollected: number | undefined, note: string) {
    if (!deliveryDialog) return;
    try {
      setError(null);
      await updateShipmentStatus(deliveryDialog.shipment.id, {
        status: 'delivered',
        cash_collected_etb: cashCollected,
        cash_note: note || undefined,
      });
      await loadShipments();
    } catch (err) {
      setError(apiErrorMessage(err, 'Failed to confirm the delivery'));
    } finally {
      setDeliveryDialog(null);
    }
  }

  async function onDelayConfirm(reason: string) {
    if (!delayDialog) return;
    try {
      setError(null);
      await updateShipmentStatus(delayDialog.shipment.id, { status: 'delayed', delay_reason: reason });
      await loadShipments();
    } catch (err) {
      setError(apiErrorMessage(err, 'Failed to update shipment status'));
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

      {deliveryDialog ? (
        <DeliveryCashDialog
          shipment={deliveryDialog.shipment}
          onConfirm={onDeliveryConfirm}
          onCancel={() => setDeliveryDialog(null)}
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
        <form className="grid grid-cols-1 gap-4 lg:grid-cols-5" onSubmit={onCreate}>
          <label className="grid gap-2 text-sm text-slate-300">
            Shipment No
            <input className="fp-input" placeholder="Shipment No" value={form.shipment_no} onChange={(e) => setForm((prev) => ({ ...prev, shipment_no: e.target.value }))} required />
          </label>
          <label className="grid gap-2 text-sm text-slate-300">
            Origin Code
            <input className="fp-input" placeholder="Origin Code" value={form.origin_warehouse_code} onChange={(e) => setForm((prev) => ({ ...prev, origin_warehouse_code: e.target.value.toUpperCase() }))} required />
          </label>
          <label className="grid gap-2 text-sm text-slate-300">
            Destination Code
            <input className="fp-input" placeholder="Destination Code" value={form.destination_warehouse_code} onChange={(e) => setForm((prev) => ({ ...prev, destination_warehouse_code: e.target.value.toUpperCase() }))} required />
          </label>
          <label className="grid gap-2 text-sm text-slate-300">
            SKU
            <input className="fp-input" placeholder="SKU" value={form.sku} onChange={(e) => setForm((prev) => ({ ...prev, sku: e.target.value.toUpperCase() }))} required />
          </label>
          <label className="grid gap-2 text-sm text-slate-300">
            Quantity
            <input className="fp-input" type="number" min={1} value={form.quantity_units} onChange={(e) => setForm((prev) => ({ ...prev, quantity_units: Number(e.target.value) }))} required />
          </label>
          <label className="grid gap-2 text-sm text-slate-300">
            Driver
            <select className="fp-input" value={form.driver_id} onChange={(e) => setForm((prev) => ({ ...prev, driver_id: e.target.value }))}>
              <option value="">Unassigned</option>
              {drivers.map((driver) => (
                <option key={driver.id} value={driver.id}>
                  {driver.full_name}
                  {driver.vehicle_plate ? ` · ${driver.vehicle_plate}` : ''}
                </option>
              ))}
            </select>
          </label>
          <label className="grid gap-2 text-sm text-slate-300">
            Cash on delivery (ETB)
            <input
              className="fp-input"
              type="number"
              min={0}
              step="0.01"
              value={form.cod_amount_etb}
              onChange={(e) => setForm((prev) => ({ ...prev, cod_amount_etb: Number(e.target.value) }))}
            />
          </label>
          <div className="flex justify-end lg:col-span-5">
            <button
              type="submit"
              disabled={creating}
              className="glow-ring inline-flex min-h-12 items-center justify-center gap-2 rounded-lg bg-sky-500 px-5 text-sm font-semibold text-slate-950 transition-colors hover:bg-sky-400 disabled:cursor-not-allowed disabled:opacity-60"
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
              <SkeletonBlock key={i} className="h-[120px]" />
            ))}
          </div>
        ) : null}

        <div className="space-y-3">
          {shipments.map((shipment) => (
            <article key={shipment.id} className="fp-row">
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div>
                  <div className="flex flex-wrap items-center gap-2">
                    <StatusBadge label={shipment.status} tone={statusTone(shipment.status)} />
                    <span className="text-xs uppercase tracking-[0.18em] text-slate-500">{new Date(shipment.created_at).toLocaleString()}</span>
                  </div>
                  <h3 className="mt-1.5 font-['Space_Grotesk'] text-lg font-semibold text-slate-50">{shipment.shipment_no}</h3>
                </div>
                <div className="text-right font-mono text-sm text-slate-400 tabular-nums">
                  <p>{shipment.origin_warehouse_code} → {shipment.destination_warehouse_code}</p>
                  <p>{shipment.sku} · {shipment.quantity_units} units</p>
                  <p className={shipment.driver_name ? 'text-slate-300' : 'text-slate-500'}>
                    {shipment.driver_name || 'No driver assigned'}
                  </p>
                  {Number(shipment.cod_amount_etb ?? 0) > 0 ? (
                    <p className="text-amber-300">COD {Number(shipment.cod_amount_etb).toFixed(2)} ETB</p>
                  ) : null}
                </div>
              </div>

              <p className="mt-2 text-sm leading-6 text-slate-400">
                {shipment.delay_reason ? `Delay note: ${shipment.delay_reason}` : 'No delay reason logged for this shipment.'}
              </p>

              <div className="mt-3 flex flex-wrap gap-2">
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
            <div className="fp-nested-surface p-6 text-center">
              <p className="font-['Space_Grotesk'] text-lg font-semibold text-slate-300">No shipments yet</p>
              <p className="mt-1 text-sm text-slate-500">Create your first shipment using the form above.</p>
            </div>
          ) : null}
        </div>
      </Panel>
    </div>
  );
}

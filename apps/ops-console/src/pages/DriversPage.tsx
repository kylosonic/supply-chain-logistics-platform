import { FormEvent, useEffect, useState } from 'react';

import { Dialog } from '../components/ui/Dialog';
import { MetricTile } from '../components/ui/MetricTile';
import { PageHeader } from '../components/ui/PageHeader';
import { Panel } from '../components/ui/Panel';
import { StatusBadge } from '../components/ui/StatusBadge';
import { useAuth } from '../context/AuthContext';
import { apiErrorMessage } from '../services/authErrors';
import {
  createDriver,
  deactivateDriver,
  declareCash,
  getCashLedger,
  listCashCollections,
  listDriverShipments,
  listDrivers,
  settleCash,
} from '../services/logisticsApi';
import type {
  CashCollection,
  CashLedgerSummary,
  CashCollectionStatus,
  Driver,
  DriverShipment,
  DriverStatus,
} from '../types/api';

/**
 * Driver roster and end-of-day cash position (NB-86).
 *
 * The operator question this page answers is asked twice a day and in two
 * directions: in the morning, *who is carrying what*, and at closing, *how much
 * cash is still out with drivers and how much never came back*. Both are cash
 * risk in this market, so they live on one surface rather than behind a filter.
 */

const EMPTY_LEDGER: CashLedgerSummary = {
  outstanding_count: 0,
  outstanding_expected_etb: '0.00',
  collected_count: 0,
  collected_etb: '0.00',
  settled_count: 0,
  settled_etb: '0.00',
  shortfall_etb: '0.00',
};

function driverTone(status: DriverStatus) {
  return status === 'active' ? 'success' : 'neutral';
}

function cashTone(status: CashCollectionStatus) {
  if (status === 'settled') return 'success';
  if (status === 'outstanding') return 'warning';
  if (status === 'voided') return 'danger';
  return 'info';
}

/** Money is summed as a decimal string on the server; this only formats it. */
function etb(value: string | number | null | undefined): string {
  const parsed = Number(value ?? 0);
  if (!Number.isFinite(parsed)) return '0.00 ETB';
  return `${parsed.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })} ETB`;
}

function SkeletonBlock({ className }: { className?: string }) {
  return <div className={`skeleton ${className ?? ''}`} />;
}

function DeclareCashDialog({
  record,
  onConfirm,
  onCancel,
}: {
  record: CashCollection;
  onConfirm: (collected: number, note: string) => void;
  onCancel: () => void;
}) {
  const [collected, setCollected] = useState<string>(record.collected_etb ?? '0');
  const [note, setNote] = useState('');

  const expected = Number(record.expected_etb ?? 0);
  const entered = Number(collected);
  const shortfall = Number.isFinite(entered) ? Math.max(0, expected - entered) : 0;

  return (
    <Dialog
      eyebrow="Cash declaration"
      title={`Record cash for ${record.shipment_no}`}
      description={`Expected at the door: ${etb(record.expected_etb)}. Enter what the driver is actually holding — a shortfall is recorded, not hidden.`}
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
            onClick={() => onConfirm(entered, note)}
            disabled={!Number.isFinite(entered) || entered < 0}
            className="glow-ring inline-flex min-h-10 items-center justify-center rounded-lg bg-sky-500 px-5 text-sm font-semibold text-slate-950 transition-colors hover:bg-sky-400 disabled:cursor-not-allowed disabled:opacity-60"
          >
            Record cash
          </button>
        </>
      }
    >
      <div className="grid gap-4">
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
        <label className="grid gap-2 text-sm text-slate-300">
          Note (optional)
          <textarea
            className="fp-input min-h-20 px-4 py-3"
            placeholder="Anything the office should know about this collection..."
            value={note}
            onChange={(e) => setNote(e.target.value)}
          />
        </label>
        <p className={`text-sm ${shortfall > 0 ? 'text-amber-300' : 'text-slate-400'}`}>
          {shortfall > 0
            ? `Shortfall of ${etb(shortfall)} will be recorded against this delivery.`
            : 'This clears the expected amount in full.'}
        </p>
      </div>
    </Dialog>
  );
}

function SettleCashDialog({
  record,
  onConfirm,
  onCancel,
}: {
  record: CashCollection;
  onConfirm: (note: string) => void;
  onCancel: () => void;
}) {
  const [note, setNote] = useState('');

  return (
    <Dialog
      eyebrow="Office close"
      title={`Settle cash for ${record.shipment_no}`}
      description="Confirms the cash is in hand. Settling closes the record and keeps any shortfall on the books — write-offs are never erased from the month-end figure."
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
            onClick={() => onConfirm(note)}
            className="glow-ring inline-flex min-h-10 items-center justify-center rounded-lg bg-sky-500 px-5 text-sm font-semibold text-slate-950 transition-colors hover:bg-sky-400"
          >
            Settle
          </button>
        </>
      }
    >
      <label className="grid gap-2 text-sm text-slate-300">
        Settlement note (optional)
        <textarea
          autoFocus
          className="fp-input min-h-20 px-4 py-3"
          placeholder="e.g. Cash banked with the CBE deposit on Monday."
          value={note}
          onChange={(e) => setNote(e.target.value)}
        />
      </label>
    </Dialog>
  );
}

export function DriversPage() {
  const { user } = useAuth();
  const isAdmin = user?.role === 'admin';

  const [drivers, setDrivers] = useState<Driver[]>([]);
  const [ledger, setLedger] = useState<CashLedgerSummary>(EMPTY_LEDGER);
  const [collections, setCollections] = useState<CashCollection[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  const [van, setVan] = useState<{ driverName: string; shipments: DriverShipment[] } | null>(null);
  const [declareTarget, setDeclareTarget] = useState<CashCollection | null>(null);
  const [settleTarget, setSettleTarget] = useState<CashCollection | null>(null);

  const [form, setForm] = useState({
    full_name: '',
    phone: '',
    license_no: '',
    vehicle_plate: '',
    notes: '',
  });

  async function loadAll() {
    try {
      setError(null);
      const [roster, ledgerRow, cash] = await Promise.all([
        listDrivers(),
        getCashLedger(),
        listCashCollections(),
      ]);
      setDrivers(roster);
      setLedger(ledgerRow);
      setCollections(cash);
    } catch (err) {
      setError(apiErrorMessage(err, 'Failed to load the driver roster and cash ledger'));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadAll();
  }, []);

  async function onCreateDriver(event: FormEvent) {
    event.preventDefault();
    try {
      setSaving(true);
      setError(null);
      await createDriver({
        full_name: form.full_name,
        phone: form.phone,
        license_no: form.license_no || undefined,
        vehicle_plate: form.vehicle_plate || undefined,
        notes: form.notes || undefined,
      });
      setForm({ full_name: '', phone: '', license_no: '', vehicle_plate: '', notes: '' });
      await loadAll();
    } catch (err) {
      setError(apiErrorMessage(err, 'Failed to add the driver'));
    } finally {
      setSaving(false);
    }
  }

  async function onDeactivate(driver: Driver) {
    try {
      setError(null);
      await deactivateDriver(driver.id);
      await loadAll();
    } catch (err) {
      setError(apiErrorMessage(err, 'Failed to deactivate the driver'));
    }
  }

  async function onShowVan(driver: Driver) {
    try {
      setError(null);
      const shipments = await listDriverShipments(driver.id);
      setVan({ driverName: driver.full_name, shipments });
    } catch (err) {
      setError(apiErrorMessage(err, 'Failed to load what this driver is carrying'));
    }
  }

  async function onDeclareConfirm(collected: number, note: string) {
    if (!declareTarget) return;
    try {
      setError(null);
      await declareCash(declareTarget.id, { collected_etb: collected, note: note || undefined });
      await loadAll();
    } catch (err) {
      setError(apiErrorMessage(err, 'Failed to record the cash declaration'));
    } finally {
      setDeclareTarget(null);
    }
  }

  async function onSettleConfirm(note: string) {
    if (!settleTarget) return;
    try {
      setError(null);
      await settleCash(settleTarget.id, { note: note || undefined });
      await loadAll();
    } catch (err) {
      setError(apiErrorMessage(err, 'Failed to settle this cash record'));
    } finally {
      setSettleTarget(null);
    }
  }

  const activeCount = drivers.filter((driver) => driver.status === 'active').length;
  const shortfall = Number(ledger.shortfall_etb ?? 0);

  return (
    <div className="space-y-6">
      {declareTarget ? (
        <DeclareCashDialog
          record={declareTarget}
          onConfirm={onDeclareConfirm}
          onCancel={() => setDeclareTarget(null)}
        />
      ) : null}

      {settleTarget ? (
        <SettleCashDialog
          record={settleTarget}
          onConfirm={onSettleConfirm}
          onCancel={() => setSettleTarget(null)}
        />
      ) : null}

      <PageHeader
        eyebrow="Fleet and cash"
        title="Know who is carrying the load and what cash is coming back"
        description="Keep the driver roster current, see what each driver has on the van, and close the day knowing exactly how much cash is still out and how much is missing."
      />

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <MetricTile
          title="Active drivers"
          value={activeCount}
          detail={`${drivers.length} on the roster in total.`}
          tone="info"
        />
        <MetricTile
          title="Cash with drivers"
          value={etb(ledger.outstanding_expected_etb)}
          detail={`${ledger.outstanding_count} deliveries awaiting a cash figure.`}
          tone={ledger.outstanding_count > 0 ? 'warning' : 'neutral'}
        />
        <MetricTile
          title="Collected, not banked"
          value={etb(ledger.collected_etb)}
          detail={`${ledger.collected_count} collections recorded and not yet settled.`}
          tone="neutral"
        />
        <MetricTile
          title="Shortfall"
          value={etb(ledger.shortfall_etb)}
          detail={
            shortfall > 0
              ? 'Collected short of the expected amount. Still on the books.'
              : 'Every collection matches what was expected.'
          }
          tone={shortfall > 0 ? 'danger' : 'success'}
        />
      </div>

      {error ? <p className="text-sm text-rose-300">{error}</p> : null}

      <Panel
        eyebrow="Roster"
        title="Add a driver"
        description="Phone number is how a driver is identified day to day, so it is the one field that must be right."
      >
        <form className="grid grid-cols-1 gap-4 lg:grid-cols-5" onSubmit={onCreateDriver}>
          <label className="grid gap-2 text-sm text-slate-300">
            Full name
            <input
              className="fp-input"
              placeholder="Yohannes Tesfaye"
              value={form.full_name}
              onChange={(e) => setForm((prev) => ({ ...prev, full_name: e.target.value }))}
              required
            />
          </label>
          <label className="grid gap-2 text-sm text-slate-300">
            Phone
            <input
              className="fp-input"
              placeholder="+251911000001"
              value={form.phone}
              onChange={(e) => setForm((prev) => ({ ...prev, phone: e.target.value }))}
              required
            />
          </label>
          <label className="grid gap-2 text-sm text-slate-300">
            Licence no
            <input
              className="fp-input"
              placeholder="ET-DRV-00000"
              value={form.license_no}
              onChange={(e) => setForm((prev) => ({ ...prev, license_no: e.target.value }))}
            />
          </label>
          <label className="grid gap-2 text-sm text-slate-300">
            Vehicle plate
            <input
              className="fp-input"
              placeholder="AA-3-B12345"
              value={form.vehicle_plate}
              onChange={(e) => setForm((prev) => ({ ...prev, vehicle_plate: e.target.value }))}
            />
          </label>
          <label className="grid gap-2 text-sm text-slate-300">
            Notes
            <input
              className="fp-input"
              placeholder="Assigned to the Bole run"
              value={form.notes}
              onChange={(e) => setForm((prev) => ({ ...prev, notes: e.target.value }))}
            />
          </label>
          <div className="flex justify-end lg:col-span-5">
            <button
              type="submit"
              disabled={saving}
              className="glow-ring inline-flex min-h-12 items-center justify-center gap-2 rounded-lg bg-sky-500 px-5 text-sm font-semibold text-slate-950 transition-colors hover:bg-sky-400 disabled:cursor-not-allowed disabled:opacity-60"
            >
              {saving ? (
                <svg className="animate-spin-slow h-4 w-4" viewBox="0 0 24 24" fill="none">
                  <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeDasharray="50 20" />
                </svg>
              ) : null}
              {saving ? 'Adding...' : 'Add driver'}
            </button>
          </div>
        </form>
      </Panel>

      <Panel
        eyebrow="Roster"
        title="Who is on the fleet today"
        description="Open a driver to see what they are carrying right now, without reading the whole shipment board."
      >
        {loading ? (
          <div className="space-y-3">
            {[1, 2].map((i) => (
              <SkeletonBlock key={i} className="h-[96px]" />
            ))}
          </div>
        ) : null}

        <div className="space-y-3">
          {drivers.map((driver) => (
            <article key={driver.id} className="fp-row">
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div>
                  <div className="flex flex-wrap items-center gap-2">
                    <StatusBadge label={driver.status} tone={driverTone(driver.status)} />
                    <span className="font-mono text-xs text-slate-500">{driver.phone}</span>
                  </div>
                  <h3 className="mt-1.5 font-['Space_Grotesk'] text-lg font-semibold text-slate-50">
                    {driver.full_name}
                  </h3>
                </div>
                <div className="text-right font-mono text-sm text-slate-400 tabular-nums">
                  <p>{driver.vehicle_plate || 'No plate on file'}</p>
                  <p>{driver.license_no || 'No licence on file'}</p>
                </div>
              </div>

              {driver.notes ? (
                <p className="mt-2 text-sm leading-6 text-slate-400">{driver.notes}</p>
              ) : null}

              <div className="mt-3 flex flex-wrap gap-2">
                <button
                  type="button"
                  onClick={() => onShowVan(driver)}
                  className="glow-ring rounded-full border border-slate-700 px-3 py-2 text-xs font-semibold text-slate-200 transition hover:border-slate-500 hover:bg-slate-950"
                >
                  What is on the van
                </button>
                {isAdmin && driver.status === 'active' ? (
                  <button
                    type="button"
                    onClick={() => onDeactivate(driver)}
                    className="glow-ring rounded-full border border-slate-700 px-3 py-2 text-xs font-semibold text-slate-300 transition hover:border-rose-500/50 hover:bg-rose-950/20 hover:text-rose-200"
                  >
                    Deactivate
                  </button>
                ) : null}
              </div>
            </article>
          ))}

          {!loading && drivers.length === 0 ? (
            <div className="fp-nested-surface p-6 text-center">
              <p className="font-['Space_Grotesk'] text-lg font-semibold text-slate-300">No drivers on the roster</p>
              <p className="mt-1 text-sm text-slate-500">
                Add your first driver above. A fleet CSV upload does not create drivers — the roster is maintained here.
              </p>
            </div>
          ) : null}
        </div>
      </Panel>

      {van ? (
        <Panel
          eyebrow="Load in hand"
          title={`What ${van.driverName} is carrying`}
          description="Open shipments assigned to this driver, newest schedule first."
        >
          <div className="space-y-3">
            {van.shipments.map((shipment) => (
              <div key={shipment.id} className="fp-nested-surface flex flex-wrap items-center justify-between gap-3 px-4 py-3">
                <div className="flex items-center gap-3">
                  <StatusBadge label={shipment.status} tone={shipment.status === 'delivered' ? 'success' : 'info'} />
                  <span className="font-mono text-sm text-slate-200">{shipment.shipment_no}</span>
                </div>
                <span className="font-mono text-sm text-slate-400 tabular-nums">
                  COD {etb(shipment.cod_amount_etb)}
                </span>
              </div>
            ))}
            {van.shipments.length === 0 ? (
              <p className="text-sm text-slate-400">Nothing assigned to this driver right now.</p>
            ) : null}
            <div className="flex justify-end">
              <button
                type="button"
                onClick={() => setVan(null)}
                className="glow-ring rounded-full border border-slate-700 px-3 py-2 text-xs font-semibold text-slate-200 transition hover:border-slate-500 hover:bg-slate-950"
              >
                Close
              </button>
            </div>
          </div>
        </Panel>
      ) : null}

      <Panel
        eyebrow="End of day"
        title="Cash position"
        description="Every delivery that expects cash at the door. Record what the driver is holding, then settle it once the office has the money."
      >
        <div className="space-y-3">
          {collections.map((record) => (
            <article key={record.id} className="fp-row">
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div>
                  <div className="flex flex-wrap items-center gap-2">
                    <StatusBadge label={record.status} tone={cashTone(record.status)} />
                    <span className="font-mono text-xs text-slate-500">{record.shipment_no}</span>
                  </div>
                  <h3 className="mt-1.5 font-['Space_Grotesk'] text-lg font-semibold text-slate-50">
                    {record.driver_name || 'Unassigned driver'}
                  </h3>
                </div>
                <div className="text-right font-mono text-sm text-slate-400 tabular-nums">
                  <p>Expected {etb(record.expected_etb)}</p>
                  <p>Collected {etb(record.collected_etb)}</p>
                  <p className={Number(record.shortfall_etb ?? 0) > 0 ? 'text-amber-300' : 'text-slate-500'}>
                    Shortfall {etb(record.shortfall_etb)}
                  </p>
                </div>
              </div>

              {record.note ? <p className="mt-2 text-sm leading-6 text-slate-400">{record.note}</p> : null}

              <div className="mt-3 flex flex-wrap gap-2">
                {record.status === 'outstanding' ? (
                  <button
                    type="button"
                    onClick={() => setDeclareTarget(record)}
                    className="glow-ring rounded-full border border-slate-700 px-3 py-2 text-xs font-semibold text-slate-200 transition hover:border-slate-500 hover:bg-slate-950"
                  >
                    Record cash
                  </button>
                ) : null}
                {isAdmin && record.status !== 'settled' && record.status !== 'voided' ? (
                  <button
                    type="button"
                    onClick={() => setSettleTarget(record)}
                    className="glow-ring rounded-full border border-emerald-500/30 px-3 py-2 text-xs font-semibold text-emerald-200 transition hover:border-emerald-400/50 hover:bg-emerald-950/20"
                  >
                    Settle
                  </button>
                ) : null}
              </div>
            </article>
          ))}

          {!loading && collections.length === 0 ? (
            <div className="fp-nested-surface p-6 text-center">
              <p className="font-['Space_Grotesk'] text-lg font-semibold text-slate-300">No cash expected right now</p>
              <p className="mt-1 text-sm text-slate-500">
                A cash record opens when a cash-on-delivery shipment is marked delivered on the Shipments board.
              </p>
            </div>
          ) : null}
        </div>

        <p className="mt-4 text-sm text-slate-500">
          Settled to date: <span className="font-mono text-slate-300">{etb(ledger.settled_etb)}</span> across{' '}
          {ledger.settled_count} collections.
        </p>
      </Panel>
    </div>
  );
}

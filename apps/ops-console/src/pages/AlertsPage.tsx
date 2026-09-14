import { FormEvent, useCallback, useEffect, useState } from 'react';

import { Dialog } from '../components/ui/Dialog';
import { MetricTile } from '../components/ui/MetricTile';
import { PageHeader } from '../components/ui/PageHeader';
import { Panel } from '../components/ui/Panel';
import { StatusBadge } from '../components/ui/StatusBadge';
import { acknowledgeAlert, autoResolveAlert, createAlert, listAlerts, resolveAlert, scanAlerts } from '../services/logisticsApi';
import type { Alert, AlertStatus, AlertSeverity } from '../types/api';
import { apiErrorMessage } from '../services/authErrors';

function severityTone(severity: AlertSeverity) {
  if (severity === 'critical') return 'danger';
  if (severity === 'high') return 'warning';
  if (severity === 'medium') return 'info';
  return 'neutral';
}

function statusTone(status: AlertStatus) {
  if (status === 'resolved') return 'success';
  if (status === 'acknowledged') return 'info';
  return 'warning';
}

/* ── Inline resolution note dialog ─────────────────────────── */

function ResolveDialog({
  alertTitle,
  onConfirm,
  onCancel,
}: {
  alertTitle: string;
  onConfirm: (note: string | undefined) => void;
  onCancel: () => void;
}) {
  const [note, setNote] = useState('');

  return (
    <Dialog
      eyebrow="Resolution"
      title={`Resolve: ${alertTitle}`}
      description="Optionally provide a resolution note to document how this alert was handled."
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
            onClick={() => onConfirm(note.trim() || undefined)}
            className="glow-ring inline-flex min-h-10 items-center justify-center rounded-lg bg-emerald-500 px-5 text-sm font-semibold text-slate-950 transition-colors hover:bg-emerald-400"
          >
            Resolve alert
          </button>
        </>
      }
    >
      <textarea
        autoFocus
        className="fp-input min-h-24 px-4 py-3"
        placeholder="Resolution note (optional)..."
        value={note}
        onChange={(e) => setNote(e.target.value)}
      />
    </Dialog>
  );
}

export function AlertsPage() {
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [statusFilter, setStatusFilter] = useState<AlertStatus | 'all'>('open');
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [isScanning, setIsScanning] = useState(false);
  const [resolveDialog, setResolveDialog] = useState<{ alert: Alert } | null>(null);
  const [form, setForm] = useState({ title: '', message: '', severity: 'medium' as AlertSeverity });

  // NB-77 lint gate: memoise the loader so the mount effect can depend on it
  // honestly (it reads `statusFilter`), instead of suppressing the rule.
  const loadAlerts = useCallback(async (filter: AlertStatus | 'all' = statusFilter) => {
    try {
      setError(null);
      const data = await listAlerts(filter === 'all' ? undefined : filter);
      setAlerts(data);
    } catch (err) {
      setError(apiErrorMessage(err, 'Failed to load alerts'));
    } finally {
      setLoading(false);
    }
  }, [statusFilter]);

  useEffect(() => {
    void loadAlerts();
  }, [loadAlerts]);

  async function onCreate(event: FormEvent) {
    event.preventDefault();
    try {
      await createAlert(form);
      setForm({ title: '', message: '', severity: 'medium' });
      await loadAlerts();
    } catch (err) {
      setError(apiErrorMessage(err, 'Failed to create alert'));
    }
  }

  async function onScan() {
    try {
      setError(null);
      setIsScanning(true);
      await scanAlerts();
      await loadAlerts();
    } catch (err) {
      setError(apiErrorMessage(err, 'Failed to scan for alerts'));
    } finally {
      setIsScanning(false);
    }
  }

  async function onAcknowledge(alertId: string) {
    try {
      await acknowledgeAlert(alertId);
      await loadAlerts();
    } catch (err) {
      setError(apiErrorMessage(err, 'Failed to acknowledge alert'));
    }
  }

  async function onResolveConfirm(note: string | undefined) {
    if (!resolveDialog) return;
    try {
      await resolveAlert(resolveDialog.alert.id, note);
      await loadAlerts();
    } catch (err) {
      setError(apiErrorMessage(err, 'Failed to resolve alert'));
    } finally {
      setResolveDialog(null);
    }
  }

  async function onAutoResolve(alertId: string) {
    try {
      await autoResolveAlert(alertId);
      await loadAlerts();
    } catch (err) {
      setError(apiErrorMessage(err, 'Failed to auto-resolve alert'));
    }
  }

  const counts = {
    open: alerts.filter((alert) => alert.status === 'open').length,
    acknowledged: alerts.filter((alert) => alert.status === 'acknowledged').length,
    critical: alerts.filter((alert) => alert.severity === 'critical').length,
    high: alerts.filter((alert) => alert.severity === 'high').length,
  };

  // Presentation-only triage: highest severity first, then newest — render
  // order only; the server payload and filter state are never mutated.
  const severityRank: Record<AlertSeverity, number> = {
    critical: 0,
    high: 1,
    medium: 2,
    low: 3,
  };
  const sortedAlerts = [...alerts].sort(
    (a, b) =>
      severityRank[a.severity] - severityRank[b.severity] ||
      new Date(b.created_at).getTime() - new Date(a.created_at).getTime(),
  );

  return (
    <div className="space-y-6">
      {resolveDialog ? (
        <ResolveDialog
          alertTitle={resolveDialog.alert.title}
          onConfirm={onResolveConfirm}
          onCancel={() => setResolveDialog(null)}
        />
      ) : null}

      <PageHeader
        eyebrow="Exception center"
        title="Triage, assign, and close operational risk quickly"
        description="Use manual alerts for coordination, run exception scans on demand, and keep the backlog visible by severity and status."
        actions={
          <button
            onClick={onScan}
            disabled={isScanning}
            className="glow-ring inline-flex min-h-10 items-center justify-center gap-2 rounded-lg bg-sky-500 px-4 text-sm font-semibold text-slate-950 transition-colors hover:bg-sky-400 disabled:opacity-60"
          >
            {isScanning ? (
              <svg className="animate-spin-slow h-4 w-4" viewBox="0 0 24 24" fill="none"><circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeDasharray="50 20" /></svg>
            ) : null}
            {isScanning ? 'Scanning...' : 'Scan for exceptions'}
          </button>
        }
      />

      <div className="grid grid-cols-1 gap-4 xl:grid-cols-4">
        <MetricTile title="Open" value={counts.open} detail="Alerts currently waiting for first response." tone={counts.open > 0 ? 'warning' : 'success'} />
        <MetricTile title="Acknowledged" value={counts.acknowledged} detail="Items owned by the team but not yet closed." tone="info" />
        <MetricTile title="Critical" value={counts.critical} detail="Incidents with the highest operating urgency." tone={counts.critical > 0 ? 'danger' : 'neutral'} />
        <MetricTile title="High severity" value={counts.high} detail="Issues likely to impact service quality or cost if they linger." tone={counts.high > 0 ? 'warning' : 'neutral'} />
      </div>

      <div className="grid grid-cols-1 gap-5 xl:grid-cols-[0.85fr_1.15fr]">
        <Panel
          eyebrow="Manual entry"
          title="Create a manual operator alert"
          description="Use manual alerts for cross-team coordination, handoff notes, or issues detected outside automated scans."
        >
          <form className="grid grid-cols-1 gap-3" onSubmit={onCreate}>
            <input
              className="fp-input"
              placeholder="Title"
              value={form.title}
              onChange={(e) => setForm((prev) => ({ ...prev, title: e.target.value }))}
              required
            />
            <textarea
              className="fp-input min-h-32 px-4 py-3"
              placeholder="Message"
              value={form.message}
              onChange={(e) => setForm((prev) => ({ ...prev, message: e.target.value }))}
              required
            />
            <div className="flex flex-wrap gap-3">
              <select
                className="fp-input w-auto"
                value={form.severity}
                onChange={(e) => setForm((prev) => ({ ...prev, severity: e.target.value as AlertSeverity }))}
              >
                <option value="low">low</option>
                <option value="medium">medium</option>
                <option value="high">high</option>
                <option value="critical">critical</option>
              </select>
              <button className="glow-ring inline-flex min-h-12 items-center justify-center rounded-lg bg-sky-500 px-5 text-sm font-semibold text-slate-950 transition-colors hover:bg-sky-400">
                Create alert
              </button>
            </div>
          </form>
        </Panel>

        <Panel
          eyebrow="Backlog"
          title="Alert queue"
          description="Filter by lifecycle state and keep the highest-severity work visible first."
          actions={
            <select
              className="fp-input w-auto"
              value={statusFilter}
              onChange={(e) => {
                const next = e.target.value as AlertStatus | 'all';
                setStatusFilter(next);
                loadAlerts(next);
              }}
            >
              <option value="open">open</option>
              <option value="acknowledged">acknowledged</option>
              <option value="resolved">resolved</option>
              <option value="all">all</option>
            </select>
          }
        >
          {error ? <p className="text-sm text-rose-300">{error}</p> : null}
          {loading ? (
            <div className="space-y-3">
              {[1, 2, 3].map((i) => (
                <div key={i} className="skeleton h-[100px]" />
              ))}
            </div>
          ) : null}

          <div className="space-y-3">
            {sortedAlerts.map((alert) => (
              <article key={alert.id} className="fp-row">
                <div className="flex flex-wrap items-start justify-between gap-3">
                  <div className="space-y-2">
                    <div className="flex flex-wrap items-center gap-2">
                      <StatusBadge label={alert.severity} tone={severityTone(alert.severity)} />
                      <StatusBadge label={alert.status} tone={statusTone(alert.status)} />
                      <span className="text-xs uppercase tracking-[0.18em] text-slate-500">{alert.alert_type}</span>
                    </div>
                    <h3 className="font-['Space_Grotesk'] text-lg font-semibold text-slate-50">{alert.title}</h3>
                  </div>
                  <span className="text-xs text-slate-500">{new Date(alert.created_at).toLocaleString()}</span>
                </div>
                <p className="mt-2 text-sm leading-6 text-slate-400">{alert.message}</p>
                <div className="mt-3 flex flex-wrap gap-2">
                  <button
                    onClick={() => onAcknowledge(alert.id)}
                    className="glow-ring rounded-full border border-slate-700 px-3 py-2 text-xs font-semibold text-slate-200 transition hover:border-slate-500 hover:bg-slate-950 disabled:cursor-not-allowed disabled:opacity-50"
                    disabled={alert.status === 'resolved' || alert.status === 'acknowledged'}
                  >
                    Acknowledge
                  </button>
                  <button
                    onClick={() => setResolveDialog({ alert })}
                    className="glow-ring rounded-full border border-emerald-500/30 px-3 py-2 text-xs font-semibold text-emerald-200 transition hover:border-emerald-400/50 hover:bg-emerald-950/20 disabled:cursor-not-allowed disabled:opacity-50"
                    disabled={alert.status === 'resolved'}
                  >
                    Resolve
                  </button>
                  {alert.payload?.rerouting_plan ? (
                    <button
                      onClick={() => onAutoResolve(alert.id)}
                      className="glow-ring rounded-full border border-sky-500/30 px-3 py-2 text-xs font-semibold text-sky-200 transition hover:border-sky-400/50 hover:bg-sky-950/20 disabled:cursor-not-allowed disabled:opacity-50"
                      disabled={alert.status === 'resolved'}
                    >
                      Auto-Resolve
                    </button>
                  ) : null}
                </div>
              </article>
            ))}

            {!loading && alerts.length === 0 ? (
              <div className="fp-nested-surface p-6 text-center">
                <p className="font-['Space_Grotesk'] text-lg font-semibold text-slate-300">No alerts</p>
                <p className="mt-1 text-sm text-slate-500">No alerts for the selected filter.</p>
              </div>
            ) : null}
          </div>
        </Panel>
      </div>
    </div>
  );
}

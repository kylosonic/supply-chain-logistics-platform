import { FormEvent, useEffect, useState } from 'react';

import { MetricTile } from '../components/ui/MetricTile';
import { PageHeader } from '../components/ui/PageHeader';
import { Panel } from '../components/ui/Panel';
import { StatusBadge } from '../components/ui/StatusBadge';
import { acknowledgeAlert, createAlert, listAlerts, resolveAlert, scanAlerts } from '../services/logisticsApi';
import type { Alert, AlertStatus, AlertSeverity } from '../types/api';

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

const severityBorderAccent: Record<string, string> = {
  critical: 'border-l-rose-500/60',
  high: 'border-l-amber-500/60',
  medium: 'border-l-sky-500/40',
  low: 'border-l-slate-700',
};

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
    <div className="animate-fade-in fixed inset-0 z-50 grid place-items-center bg-slate-950/70 backdrop-blur-sm">
      <div className="animate-scale-in w-full max-w-lg rounded-[28px] border border-slate-800/80 bg-slate-950 p-6 shadow-[0_32px_100px_rgba(2,12,20,0.6)]">
        <p className="text-xs font-semibold uppercase tracking-[0.24em] text-emerald-300/80">Resolution</p>
        <h3 className="mt-2 font-['Space_Grotesk'] text-xl font-semibold text-slate-50">
          Resolve: {alertTitle}
        </h3>
        <p className="mt-2 text-sm text-slate-400">Optionally provide a resolution note to document how this alert was handled.</p>
        <textarea
          autoFocus
          className="mt-4 min-h-24 w-full rounded-2xl border border-slate-700 bg-slate-900/80 px-4 py-3 text-sm text-slate-100 outline-none transition focus:border-sky-400/50"
          placeholder="Resolution note (optional)..."
          value={note}
          onChange={(e) => setNote(e.target.value)}
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
            onClick={() => onConfirm(note.trim() || undefined)}
            className="glow-ring inline-flex min-h-10 items-center justify-center rounded-full bg-gradient-to-r from-emerald-400 to-teal-400 px-5 text-sm font-semibold text-slate-950 transition hover:brightness-105"
          >
            Resolve alert
          </button>
        </div>
      </div>
    </div>
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

  async function loadAlerts(filter = statusFilter) {
    try {
      setError(null);
      const data = await listAlerts(filter === 'all' ? undefined : filter);
      setAlerts(data);
    } catch (err: any) {
      setError(err?.response?.data?.detail || err?.message || 'Failed to load alerts');
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadAlerts();
  }, []);

  async function onCreate(event: FormEvent) {
    event.preventDefault();
    try {
      await createAlert(form);
      setForm({ title: '', message: '', severity: 'medium' });
      await loadAlerts();
    } catch (err: any) {
      setError(err?.response?.data?.detail || err?.message || 'Failed to create alert');
    }
  }

  async function onScan() {
    try {
      setError(null);
      setIsScanning(true);
      await scanAlerts();
      await loadAlerts();
    } catch (err: any) {
      setError(err?.response?.data?.detail || err?.message || 'Failed to scan for alerts');
    } finally {
      setIsScanning(false);
    }
  }

  async function onAcknowledge(alertId: string) {
    try {
      await acknowledgeAlert(alertId);
      await loadAlerts();
    } catch (err: any) {
      setError(err?.response?.data?.detail || err?.message || 'Failed to acknowledge alert');
    }
  }

  async function onResolveConfirm(note: string | undefined) {
    if (!resolveDialog) return;
    try {
      await resolveAlert(resolveDialog.alert.id, note);
      await loadAlerts();
    } catch (err: any) {
      setError(err?.response?.data?.detail || err?.message || 'Failed to resolve alert');
    } finally {
      setResolveDialog(null);
    }
  }

  const counts = {
    open: alerts.filter((alert) => alert.status === 'open').length,
    acknowledged: alerts.filter((alert) => alert.status === 'acknowledged').length,
    critical: alerts.filter((alert) => alert.severity === 'critical').length,
    high: alerts.filter((alert) => alert.severity === 'high').length,
  };

  const fieldClassName =
    'glow-ring min-h-12 rounded-2xl border border-slate-700 bg-slate-900/80 px-4 text-sm text-slate-100 outline-none transition focus:border-sky-400/50';

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
            className="glow-ring inline-flex min-h-10 items-center justify-center gap-2 rounded-full bg-emerald-500 px-4 text-sm font-semibold text-slate-950 transition hover:brightness-105 disabled:opacity-60"
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
              className={fieldClassName}
              placeholder="Title"
              value={form.title}
              onChange={(e) => setForm((prev) => ({ ...prev, title: e.target.value }))}
              required
            />
            <textarea
              className="glow-ring min-h-32 rounded-2xl border border-slate-700 bg-slate-900/80 px-4 py-3 text-sm text-slate-100 outline-none transition focus:border-sky-400/50"
              placeholder="Message"
              value={form.message}
              onChange={(e) => setForm((prev) => ({ ...prev, message: e.target.value }))}
              required
            />
            <div className="flex flex-wrap gap-3">
              <select
                className={fieldClassName}
                value={form.severity}
                onChange={(e) => setForm((prev) => ({ ...prev, severity: e.target.value as AlertSeverity }))}
              >
                <option value="low">low</option>
                <option value="medium">medium</option>
                <option value="high">high</option>
                <option value="critical">critical</option>
              </select>
              <button className="glow-ring inline-flex min-h-12 items-center justify-center rounded-full bg-gradient-to-r from-sky-300 via-sky-400 to-teal-300 px-5 text-sm font-semibold text-slate-950 transition hover:brightness-105">
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
              className={fieldClassName}
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
                <div key={i} className="skeleton h-[100px] rounded-[22px]" />
              ))}
            </div>
          ) : null}

          <div className="space-y-3">
            {alerts.map((alert, index) => (
              <article
                key={alert.id}
                className={`animate-fade-in hover-lift rounded-[22px] border border-l-[3px] border-slate-800 bg-slate-900/70 p-4 ${severityBorderAccent[alert.severity] ?? ''}`}
                style={{ animationDelay: `${index * 0.04}s` }}
              >
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
                <p className="mt-3 text-sm leading-6 text-slate-400">{alert.message}</p>
                <div className="mt-4 flex flex-wrap gap-2">
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
                </div>
              </article>
            ))}

            {!loading && alerts.length === 0 ? (
              <div className="animate-fade-in rounded-[22px] border border-slate-800 bg-slate-900/40 p-6 text-center">
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

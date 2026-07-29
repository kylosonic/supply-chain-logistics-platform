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

export function AlertsPage() {
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [statusFilter, setStatusFilter] = useState<AlertStatus | 'all'>('open');
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
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
      await scanAlerts();
      await loadAlerts();
    } catch (err: any) {
      setError(err?.response?.data?.detail || err?.message || 'Failed to scan for alerts');
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

  async function onResolve(alertId: string) {
    const note = window.prompt('Resolution note (optional)', '');
    try {
      await resolveAlert(alertId, note || undefined);
      await loadAlerts();
    } catch (err: any) {
      setError(err?.response?.data?.detail || err?.message || 'Failed to resolve alert');
    }
  }

  const counts = {
    open: alerts.filter((alert) => alert.status === 'open').length,
    acknowledged: alerts.filter((alert) => alert.status === 'acknowledged').length,
    critical: alerts.filter((alert) => alert.severity === 'critical').length,
    high: alerts.filter((alert) => alert.severity === 'high').length,
  };

  const fieldClassName =
    'min-h-12 rounded-2xl border border-slate-700 bg-slate-900/80 px-4 text-sm text-slate-100 outline-none transition focus:border-sky-400/50';

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Exception center"
        title="Triage, assign, and close operational risk quickly"
        description="Use manual alerts for coordination, run exception scans on demand, and keep the backlog visible by severity and status."
        actions={
          <button
            onClick={onScan}
            className="inline-flex min-h-10 items-center justify-center rounded-full bg-emerald-500 px-4 text-sm font-semibold text-slate-950 transition hover:brightness-105"
          >
            Scan for exceptions
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
              className="min-h-32 rounded-2xl border border-slate-700 bg-slate-900/80 px-4 py-3 text-sm text-slate-100 outline-none transition focus:border-sky-400/50"
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
              <button className="inline-flex min-h-12 items-center justify-center rounded-full bg-gradient-to-r from-sky-300 via-sky-400 to-teal-300 px-5 text-sm font-semibold text-slate-950 transition hover:brightness-105">
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
          {loading ? <p className="text-sm text-slate-400">Loading alerts...</p> : null}

          <div className="space-y-3">
            {alerts.map((alert) => (
              <article key={alert.id} className="rounded-[22px] border border-slate-800 bg-slate-900/70 p-4">
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
                    className="rounded-full border border-slate-700 px-3 py-2 text-xs font-semibold text-slate-200 transition hover:border-slate-500 hover:bg-slate-950 disabled:cursor-not-allowed disabled:opacity-50"
                    disabled={alert.status === 'resolved' || alert.status === 'acknowledged'}
                  >
                    Acknowledge
                  </button>
                  <button
                    onClick={() => onResolve(alert.id)}
                    className="rounded-full border border-slate-700 px-3 py-2 text-xs font-semibold text-slate-200 transition hover:border-slate-500 hover:bg-slate-950 disabled:cursor-not-allowed disabled:opacity-50"
                    disabled={alert.status === 'resolved'}
                  >
                    Resolve
                  </button>
                </div>
              </article>
            ))}

            {!loading && alerts.length === 0 ? <p className="text-sm text-slate-500">No alerts for the selected filter.</p> : null}
          </div>
        </Panel>
      </div>
    </div>
  );
}

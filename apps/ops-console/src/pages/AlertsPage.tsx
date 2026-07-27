import { FormEvent, useEffect, useState } from 'react';

import { acknowledgeAlert, createAlert, listAlerts, resolveAlert, scanAlerts } from '../services/logisticsApi';
import type { Alert, AlertStatus, AlertSeverity } from '../types/api';

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

  return (
    <div className="space-y-6">
      <div className="rounded-lg border border-slate-200 bg-white p-4">
        <h2 className="mb-3 text-sm font-semibold text-slate-700">Create Manual Alert</h2>
        <form className="grid grid-cols-1 gap-3 md:grid-cols-4" onSubmit={onCreate}>
          <input
            className="rounded border border-slate-300 px-3 py-2 text-sm"
            placeholder="Title"
            value={form.title}
            onChange={(e) => setForm((prev) => ({ ...prev, title: e.target.value }))}
            required
          />
          <input
            className="rounded border border-slate-300 px-3 py-2 text-sm md:col-span-2"
            placeholder="Message"
            value={form.message}
            onChange={(e) => setForm((prev) => ({ ...prev, message: e.target.value }))}
            required
          />
          <div className="flex gap-2">
            <select
              className="rounded border border-slate-300 px-3 py-2 text-sm"
              value={form.severity}
              onChange={(e) => setForm((prev) => ({ ...prev, severity: e.target.value as AlertSeverity }))}
            >
              <option value="low">low</option>
              <option value="medium">medium</option>
              <option value="high">high</option>
              <option value="critical">critical</option>
            </select>
            <button className="rounded bg-slate-900 px-3 py-2 text-xs font-medium text-white">Create</button>
          </div>
        </form>
      </div>

      <div className="flex flex-wrap items-center gap-3">
        <button onClick={onScan} className="rounded bg-emerald-700 px-3 py-2 text-xs font-medium text-white">
          Scan for Exceptions
        </button>
        <select
          className="rounded border border-slate-300 px-3 py-2 text-sm"
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
      </div>

      {error ? <p className="text-sm text-red-600">{error}</p> : null}
      {loading ? <p className="text-slate-600">Loading alerts...</p> : null}

      <div className="overflow-x-auto rounded-lg border border-slate-200 bg-white">
        <table className="min-w-full divide-y divide-slate-200 text-sm">
          <thead className="bg-slate-50">
            <tr>
              <th className="px-3 py-2 text-left">Type</th>
              <th className="px-3 py-2 text-left">Severity</th>
              <th className="px-3 py-2 text-left">Title</th>
              <th className="px-3 py-2 text-left">Status</th>
              <th className="px-3 py-2 text-left">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {alerts.map((alert) => (
              <tr key={alert.id}>
                <td className="px-3 py-2">{alert.alert_type}</td>
                <td className="px-3 py-2">{alert.severity}</td>
                <td className="px-3 py-2">
                  <div className="font-medium text-slate-800">{alert.title}</div>
                  <div className="text-xs text-slate-500">{alert.message}</div>
                </td>
                <td className="px-3 py-2">{alert.status}</td>
                <td className="px-3 py-2">
                  <div className="flex gap-2">
                    <button
                      onClick={() => onAcknowledge(alert.id)}
                      className="rounded border border-slate-300 px-2 py-1 text-xs hover:bg-slate-100"
                      disabled={alert.status === 'resolved' || alert.status === 'acknowledged'}
                    >
                      Acknowledge
                    </button>
                    <button
                      onClick={() => onResolve(alert.id)}
                      className="rounded border border-slate-300 px-2 py-1 text-xs hover:bg-slate-100"
                      disabled={alert.status === 'resolved'}
                    >
                      Resolve
                    </button>
                  </div>
                </td>
              </tr>
            ))}
            {alerts.length === 0 ? (
              <tr>
                <td colSpan={5} className="px-3 py-6 text-center text-slate-500">
                  No alerts for selected filter.
                </td>
              </tr>
            ) : null}
          </tbody>
        </table>
      </div>
    </div>
  );
}

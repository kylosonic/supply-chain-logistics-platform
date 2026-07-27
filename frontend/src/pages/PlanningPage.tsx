import { useEffect, useState } from 'react';

import { useAuth } from '../context/AuthContext';
import {
  approveReplenishmentPlan,
  generateReplenishmentPlans,
  listReplenishmentPlans,
  rejectReplenishmentPlan,
} from '../services/logisticsApi';
import type { ReplenishmentPlan } from '../types/api';

export function PlanningPage() {
  const { user } = useAuth();
  const [plans, setPlans] = useState<ReplenishmentPlan[]>([]);
  const [horizon, setHorizon] = useState(4);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  async function loadPlans() {
    try {
      setError(null);
      const data = await listReplenishmentPlans();
      setPlans(data);
    } catch (err: any) {
      setError(err?.response?.data?.detail || err?.message || 'Failed to load plans');
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadPlans();
  }, []);

  async function onGenerate() {
    try {
      setError(null);
      await generateReplenishmentPlans(horizon);
      await loadPlans();
    } catch (err: any) {
      setError(err?.response?.data?.detail || err?.message || 'Failed to generate plans');
    }
  }

  async function onApprove(planId: string) {
    try {
      await approveReplenishmentPlan(planId);
      await loadPlans();
    } catch (err: any) {
      setError(err?.response?.data?.detail || err?.message || 'Failed to approve plan');
    }
  }

  async function onReject(planId: string) {
    const reason = window.prompt('Reason for rejection', 'Need manual review');
    if (!reason) return;
    try {
      await rejectReplenishmentPlan(planId, reason);
      await loadPlans();
    } catch (err: any) {
      setError(err?.response?.data?.detail || err?.message || 'Failed to reject plan');
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3 rounded-lg border border-slate-200 bg-white p-4">
        <label className="text-sm text-slate-700" htmlFor="horizon">
          Horizon (weeks)
        </label>
        <input
          id="horizon"
          type="number"
          min={1}
          max={12}
          value={horizon}
          onChange={(e) => setHorizon(Number(e.target.value))}
          className="w-20 rounded border border-slate-300 px-3 py-2 text-sm"
        />
        <button onClick={onGenerate} className="rounded bg-slate-900 px-3 py-2 text-xs font-medium text-white">
          Generate Replenishment Suggestions
        </button>
      </div>

      {error ? <p className="text-sm text-red-600">{error}</p> : null}
      {loading ? <p className="text-slate-600">Loading plans...</p> : null}

      <div className="overflow-x-auto rounded-lg border border-slate-200 bg-white">
        <table className="min-w-full divide-y divide-slate-200 text-sm">
          <thead className="bg-slate-50">
            <tr>
              <th className="px-3 py-2 text-left">Warehouse</th>
              <th className="px-3 py-2 text-left">SKU</th>
              <th className="px-3 py-2 text-left">Avg Weekly Demand</th>
              <th className="px-3 py-2 text-left">Suggested</th>
              <th className="px-3 py-2 text-left">Status</th>
              <th className="px-3 py-2 text-left">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {plans.map((plan) => (
              <tr key={plan.id}>
                <td className="px-3 py-2">{plan.warehouse_code}</td>
                <td className="px-3 py-2">{plan.sku}</td>
                <td className="px-3 py-2">{plan.avg_weekly_demand.toFixed(2)}</td>
                <td className="px-3 py-2">{plan.suggested_quantity}</td>
                <td className="px-3 py-2">{plan.status}</td>
                <td className="px-3 py-2">
                  {user?.role === 'admin' && plan.status === 'pending_approval' ? (
                    <div className="flex gap-2">
                      <button
                        onClick={() => onApprove(plan.id)}
                        className="rounded border border-slate-300 px-2 py-1 text-xs hover:bg-slate-100"
                      >
                        Approve
                      </button>
                      <button
                        onClick={() => onReject(plan.id)}
                        className="rounded border border-slate-300 px-2 py-1 text-xs hover:bg-slate-100"
                      >
                        Reject
                      </button>
                    </div>
                  ) : (
                    <span className="text-xs text-slate-500">{plan.rejection_reason || '-'}</span>
                  )}
                </td>
              </tr>
            ))}
            {plans.length === 0 ? (
              <tr>
                <td colSpan={6} className="px-3 py-6 text-center text-slate-500">
                  No replenishment plans yet.
                </td>
              </tr>
            ) : null}
          </tbody>
        </table>
      </div>
    </div>
  );
}

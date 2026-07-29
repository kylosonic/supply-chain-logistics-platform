import { useEffect, useState } from 'react';

import { MetricTile } from '../components/ui/MetricTile';
import { PageHeader } from '../components/ui/PageHeader';
import { Panel } from '../components/ui/Panel';
import { StatusBadge } from '../components/ui/StatusBadge';
import { useAuth } from '../context/AuthContext';
import {
  approveReplenishmentPlan,
  generateReplenishmentPlans,
  listReplenishmentPlans,
  rejectReplenishmentPlan,
} from '../services/logisticsApi';
import type { ReplenishmentPlan } from '../types/api';

function statusTone(status: ReplenishmentPlan['status']) {
  if (status === 'approved') return 'success';
  if (status === 'rejected') return 'danger';
  return 'warning';
}

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

  const counts = {
    pending: plans.filter((plan) => plan.status === 'pending_approval').length,
    approved: plans.filter((plan) => plan.status === 'approved').length,
    rejected: plans.filter((plan) => plan.status === 'rejected').length,
  };

  const fieldClassName =
    'min-h-12 rounded-2xl border border-slate-700 bg-slate-900/80 px-4 text-sm text-slate-100 outline-none transition focus:border-sky-400/50';

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Planning"
        title="Generate and approve replenishment actions"
        description="Keep demand pressure, approval load, and plan rationale visible so replenishment work does not become a spreadsheet side-channel."
      />

      <div className="grid grid-cols-1 gap-4 xl:grid-cols-4">
        <MetricTile title="Horizon" value={`${horizon} weeks`} detail="Current planning horizon for the next generated run." tone="info" />
        <MetricTile title="Pending" value={counts.pending} detail="Plans waiting for admin review." tone={counts.pending > 0 ? 'warning' : 'success'} />
        <MetricTile title="Approved" value={counts.approved} detail="Suggestions already accepted into the operating plan." tone="success" />
        <MetricTile title="Rejected" value={counts.rejected} detail="Suggestions sent back for manual review or correction." tone="danger" />
      </div>

      <Panel
        eyebrow="Generate"
        title="Run replenishment planning"
        description="Generate a fresh suggestion set using the selected horizon and the latest inventory and forecast posture."
      >
        <div className="flex flex-wrap items-center gap-3">
          <label className="grid gap-2 text-sm text-slate-300" htmlFor="horizon">
            Horizon (weeks)
            <input
              id="horizon"
              type="number"
              min={1}
              max={12}
              value={horizon}
              onChange={(e) => setHorizon(Number(e.target.value))}
              className={`${fieldClassName} w-28`}
            />
          </label>
          <button
            onClick={onGenerate}
            className="inline-flex min-h-12 items-center justify-center rounded-full bg-gradient-to-r from-sky-300 via-sky-400 to-teal-300 px-5 text-sm font-semibold text-slate-950 transition hover:brightness-105"
          >
            Generate replenishment suggestions
          </button>
        </div>
      </Panel>

      {error ? <p className="text-sm text-rose-300">{error}</p> : null}
      {loading ? <p className="text-sm text-slate-400">Loading plans...</p> : null}

      <Panel
        eyebrow="Approval board"
        title="Current replenishment plans"
        description="Review average demand, suggested quantity, and approval status before committing inventory moves."
      >
        <div className="space-y-3">
          {plans.map((plan) => (
            <article key={plan.id} className="rounded-[22px] border border-slate-800 bg-slate-900/70 p-4">
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div>
                  <div className="flex flex-wrap items-center gap-2">
                    <StatusBadge label={plan.status} tone={statusTone(plan.status)} />
                    <span className="text-xs uppercase tracking-[0.18em] text-slate-500">{plan.warehouse_code}</span>
                  </div>
                  <h3 className="mt-2 font-['Space_Grotesk'] text-lg font-semibold text-slate-50">{plan.sku}</h3>
                </div>
                <div className="grid gap-1 text-right text-sm text-slate-400 sm:grid-cols-3 sm:text-left">
                  <span>Avg demand: {plan.avg_weekly_demand.toFixed(2)}</span>
                  <span>Suggested: {plan.suggested_quantity}</span>
                  <span>Horizon: {plan.horizon_weeks} weeks</span>
                </div>
              </div>

              <p className="mt-3 text-sm leading-6 text-slate-400">{plan.rationale}</p>

              <div className="mt-4 flex flex-wrap items-center gap-2">
                {user?.role === 'admin' && plan.status === 'pending_approval' ? (
                  <>
                    <button
                      onClick={() => onApprove(plan.id)}
                      className="rounded-full border border-slate-700 px-3 py-2 text-xs font-semibold text-slate-200 transition hover:border-slate-500 hover:bg-slate-950"
                    >
                      Approve
                    </button>
                    <button
                      onClick={() => onReject(plan.id)}
                      className="rounded-full border border-slate-700 px-3 py-2 text-xs font-semibold text-slate-200 transition hover:border-slate-500 hover:bg-slate-950"
                    >
                      Reject
                    </button>
                  </>
                ) : (
                  <span className="text-xs text-slate-500">{plan.rejection_reason || 'No rejection reason recorded.'}</span>
                )}
              </div>
            </article>
          ))}

          {!loading && plans.length === 0 ? <p className="text-sm text-slate-500">No replenishment plans yet.</p> : null}
        </div>
      </Panel>
    </div>
  );
}

import { useEffect, useState } from 'react';

import { Dialog } from '../components/ui/Dialog';
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

/* ── Inline rejection reason dialog ────────────────────────── */

function RejectDialog({
  sku,
  onConfirm,
  onCancel,
}: {
  sku: string;
  onConfirm: (reason: string) => void;
  onCancel: () => void;
}) {
  const [reason, setReason] = useState('Need manual review');

  return (
    <Dialog
      eyebrow="Plan rejection"
      title={`Reject plan for ${sku}`}
      description="Provide a rejection reason so the planning team can understand what needs review or correction."
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
            onClick={() => reason.trim() && onConfirm(reason.trim())}
            disabled={!reason.trim()}
            className="glow-ring inline-flex min-h-10 items-center justify-center rounded-lg bg-rose-600 px-5 text-sm font-semibold text-white transition-colors hover:bg-rose-500 disabled:cursor-not-allowed disabled:opacity-60"
          >
            Reject plan
          </button>
        </>
      }
    >
      <textarea
        autoFocus
        className="fp-input min-h-24 px-4 py-3"
        placeholder="Reason for rejection..."
        value={reason}
        onChange={(e) => setReason(e.target.value)}
      />
    </Dialog>
  );
}

export function PlanningPage() {
  const { user } = useAuth();
  const [plans, setPlans] = useState<ReplenishmentPlan[]>([]);
  const [horizon, setHorizon] = useState(4);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [isGenerating, setIsGenerating] = useState(false);
  const [rejectDialog, setRejectDialog] = useState<{ plan: ReplenishmentPlan } | null>(null);

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
      setIsGenerating(true);
      await generateReplenishmentPlans(horizon);
      await loadPlans();
    } catch (err: any) {
      setError(err?.response?.data?.detail || err?.message || 'Failed to generate plans');
    } finally {
      setIsGenerating(false);
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

  async function onRejectConfirm(reason: string) {
    if (!rejectDialog) return;
    try {
      await rejectReplenishmentPlan(rejectDialog.plan.id, reason);
      await loadPlans();
    } catch (err: any) {
      setError(err?.response?.data?.detail || err?.message || 'Failed to reject plan');
    } finally {
      setRejectDialog(null);
    }
  }

  const counts = {
    pending: plans.filter((plan) => plan.status === 'pending_approval').length,
    approved: plans.filter((plan) => plan.status === 'approved').length,
    rejected: plans.filter((plan) => plan.status === 'rejected').length,
  };

  return (
    <div className="space-y-6">
      {rejectDialog ? (
        <RejectDialog
          sku={rejectDialog.plan.sku}
          onConfirm={onRejectConfirm}
          onCancel={() => setRejectDialog(null)}
        />
      ) : null}

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
        <div className="flex flex-wrap items-end gap-3">
          <label className="grid gap-2 text-sm text-slate-300" htmlFor="horizon">
            Horizon (weeks)
            <input
              id="horizon"
              type="number"
              min={1}
              max={12}
              value={horizon}
              onChange={(e) => setHorizon(Number(e.target.value))}
              className="fp-input w-28"
            />
          </label>
          <button
            onClick={onGenerate}
            disabled={isGenerating}
            className="glow-ring inline-flex min-h-12 items-center justify-center gap-2 rounded-lg bg-sky-500 px-5 text-sm font-semibold text-slate-950 transition-colors hover:bg-sky-400 disabled:opacity-60"
          >
            {isGenerating ? (
              <svg className="animate-spin-slow h-4 w-4" viewBox="0 0 24 24" fill="none"><circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeDasharray="50 20" /></svg>
            ) : null}
            {isGenerating ? 'Generating...' : 'Generate replenishment suggestions'}
          </button>
        </div>
      </Panel>

      {error ? (
        <Panel className="border-rose-500/25 bg-rose-950/12">
          <p className="text-sm text-rose-200">{error}</p>
        </Panel>
      ) : null}

      {loading ? (
        <Panel eyebrow="Approval board" title="Current replenishment plans">
          <div className="space-y-3">
            {[1, 2, 3].map((i) => (
              <div key={i} className="skeleton h-[120px]" />
            ))}
          </div>
        </Panel>
      ) : null}

      {!loading ? (
        <Panel
          eyebrow="Approval board"
          title="Current replenishment plans"
          description="Review average demand, suggested quantity, and approval status before committing inventory moves."
        >
          <div className="space-y-6">
            {plans.filter((plan) => plan.status === 'pending_approval').length > 0 ? (
              <div className="space-y-3">
                {plans
                  .filter((plan) => plan.status === 'pending_approval')
                  .map((plan, index) => (
                    <PlanRow key={plan.id} plan={plan} userRole={user?.role} onApprove={onApprove} onReject={() => setRejectDialog({ plan })} index={index} />
                  ))}
              </div>
            ) : null}

            {plans.filter((plan) => plan.status !== 'pending_approval').length > 0 ? (
              <div className="space-y-3 border-t border-slate-800/70 pt-5 opacity-80">
                {plans
                  .filter((plan) => plan.status !== 'pending_approval')
                  .map((plan, index) => (
                    <PlanRow key={plan.id} plan={plan} userRole={user?.role} onApprove={onApprove} onReject={() => setRejectDialog({ plan })} index={index} />
                  ))}
              </div>
            ) : null}

            {plans.length === 0 ? (
              <div className="fp-nested-surface animate-fade-in p-6 text-center">
                <p className="font-['Space_Grotesk'] text-lg font-semibold text-slate-300">No plans yet</p>
                <p className="mt-1 text-sm text-slate-500">Generate replenishment suggestions using the form above.</p>
              </div>
            ) : null}
          </div>
        </Panel>
      ) : null}
    </div>
  );
}

function PlanRow({
  plan,
  userRole,
  onApprove,
  onReject,
  index,
}: {
  plan: ReplenishmentPlan;
  userRole: string | undefined;
  onApprove: (planId: string) => void;
  onReject: () => void;
  index: number;
}) {
  return (
    <article className="fp-row" style={{ animationDelay: `${index * 0.04}s` }}>
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <div className="flex flex-wrap items-center gap-2">
            <StatusBadge label={plan.status} tone={statusTone(plan.status)} />
            <span className="text-xs uppercase tracking-[0.18em] text-slate-500">{plan.warehouse_code}</span>
          </div>
          <h3 className="mt-1.5 font-['Space_Grotesk'] text-lg font-semibold text-slate-50">{plan.sku}</h3>
        </div>
        <div className="grid gap-1 text-right font-mono text-sm text-slate-400 tabular-nums sm:grid-cols-3 sm:text-left">
          <span>Avg demand: <span className="font-semibold text-slate-200">{plan.avg_weekly_demand.toFixed(2)}</span></span>
          <span>Suggested: <span className="font-semibold text-slate-200">{plan.suggested_quantity}</span></span>
          <span>Horizon: <span className="font-semibold text-slate-200">{plan.horizon_weeks}w</span></span>
        </div>
      </div>

      <p className="mt-2 text-sm leading-6 text-slate-400">{plan.rationale}</p>

      <div className="mt-3 flex flex-wrap items-center gap-2">
        {userRole === 'admin' && plan.status === 'pending_approval' ? (
          <>
            <button
              onClick={() => onApprove(plan.id)}
              className="glow-ring rounded-full border border-emerald-500/30 px-3 py-2 text-xs font-semibold text-emerald-200 transition hover:border-emerald-400/50 hover:bg-emerald-950/20"
            >
              Approve
            </button>
            <button
              onClick={onReject}
              className="glow-ring rounded-full border border-rose-500/30 px-3 py-2 text-xs font-semibold text-rose-200 transition hover:border-rose-400/50 hover:bg-rose-950/20"
            >
              Reject
            </button>
          </>
        ) : (
          <span className="text-xs text-slate-500">{plan.rejection_reason || 'No rejection reason recorded.'}</span>
        )}
      </div>
    </article>
  );
}

import { useMemo, useState } from 'react';
import { Link } from 'react-router-dom';

import { ActivationBanner } from '../components/ActivationBanner';
import { DecisionBriefPanel } from '../components/DecisionBriefPanel';
import { DockGanttChart } from '../components/DockGanttChart';
import { FeedbackForm } from '../components/FeedbackForm';
import { FreightReconciliationPanel } from '../components/FreightReconciliationPanel';
import { ForecastChart } from '../components/ForecastChart';
import { InventoryCharts } from '../components/InventoryCharts';
import { MetricTile } from '../components/ui/MetricTile';
import { PageHeader } from '../components/ui/PageHeader';
import { Panel } from '../components/ui/Panel';
import { StatusBadge } from '../components/ui/StatusBadge';
import {
  useActivationState,
  useAuditTimeline,
  useCurrentUsage,
  useDockAppointments,
  useExceptionFeed,
  useForecast,
  useInventoryOverview,
  useInvalidateDashboard,
  useLiveDataInvalidator,
  useReplenishmentPlans,
  useRouteSchedules,
  useShipments,
  useWeatherRiskZones,
} from '../hooks/queries';
import { useLivePayload, useLivePayloadStream } from '../hooks/useLiveUpdates';

function severityTone(severity: string) {
  if (severity === 'critical' || severity === 'danger') return 'danger';
  if (severity === 'high' || severity === 'warning') return 'warning';
  if (severity === 'medium' || severity === 'info') return 'info';
  return 'neutral';
}

function SkeletonBlock({ className }: { className?: string }) {
  return <div className={`animate-pulse rounded-[var(--fp-radius-panel)] bg-slate-800/40 ${className ?? ''}`} />;
}

// NB-29.3 panel gate map: hidden vs placeholder per surface, milestone
// threshold fixed — no per-panel configuration path (NB-29.4).
const PANEL_GATES = [
  { id: 'inventory-charts', mode: 'placeholder', milestone: 4 },
  { id: 'utilization', mode: 'placeholder', milestone: 4 },
  { id: 'forecast-chart', mode: 'placeholder', milestone: 5 },
  { id: 'forecast-demand', mode: 'placeholder', milestone: 5 },
  { id: 'weather-risk', mode: 'placeholder', milestone: 5 },
  { id: 'dock-gantt', mode: 'hidden', milestone: 6 },
  { id: 'freight-recon', mode: 'hidden', milestone: 6 },
] as const;

function gateMilestone(id: (typeof PANEL_GATES)[number]['id']) {
  return PANEL_GATES.find((gate) => gate.id === id)!.milestone;
}

export { PANEL_GATES };

function GatePlaceholder({ milestone }: { milestone: number }) {
  return (
    <div className="grid h-full min-h-[160px] place-items-center rounded-[var(--fp-radius-panel)] border border-dashed border-slate-700/60 bg-slate-900/30 p-6 text-center">
      <div>
        <p className="font-['Space_Grotesk'] text-lg font-semibold text-slate-300">
          Unlocks after Milestone {milestone}
        </p>
        <Link to="/upload" className="mt-2 inline-block text-sm font-semibold text-sky-300 underline-offset-4 hover:underline">
          Continue onboarding →
        </Link>
      </div>
    </div>
  );
}

function DashboardSkeleton() {
  return (
    <div className="space-y-6">
      <SkeletonBlock className="h-[120px] rounded-[var(--fp-radius-hero)]" />
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        {[1, 2].map((i) => (
          <SkeletonBlock key={i} className="h-[110px] rounded-[var(--fp-radius-panel)]" />
        ))}
      </div>
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-3">
        {[1, 2, 3].map((i) => (
          <SkeletonBlock key={i} className="h-[110px] rounded-[var(--fp-radius-panel)]" />
        ))}
      </div>
      <div className="grid grid-cols-1 gap-5 xl:grid-cols-[1.25fr_0.75fr]">
        <SkeletonBlock className="h-[300px] rounded-[var(--fp-radius-hero)]" />
        <SkeletonBlock className="h-[300px] rounded-[var(--fp-radius-hero)]" />
      </div>
    </div>
  );
}

export function DashboardPage() {
  const invalidateDashboard = useInvalidateDashboard();

  const inventoryQ = useInventoryOverview();
  const forecastQ = useForecast(4);
  const schedulesQ = useRouteSchedules();
  const shipmentsQ = useShipments();
  const plansQ = useReplenishmentPlans();
  const usageQ = useCurrentUsage();
  const feedQ = useExceptionFeed();
  const auditQ = useAuditTimeline();
  const riskQ = useWeatherRiskZones();
  const appointmentsQ = useDockAppointments();
  const activationQ = useActivationState();

  const [isRefreshing, setIsRefreshing] = useState(false);

  // TECH-73: the live payload comes from the session-scoped store owned by
  // SessionLiveUpdates — the chip survives page switches (decision 8) and
  // background invalidation is coalesced + payload-scoped (decisions 5/6);
  // invalidations only run while this page is mounted (stream subscription).
  const livePayload = useLivePayload();
  const invalidateLivePayload = useLiveDataInvalidator();

  useLivePayloadStream((payload) => {
    invalidateLivePayload(payload);
  });

  // NB-77 lint gate: derive each list with a stable identity. A bare
  // `data ?? []` allocates a new array on every render, so the `summary` memo
  // below would recompute on each pass and the exhaustive-deps rule flagged
  // the six list inputs as unstable dependencies.
  const inventory = useMemo(() => inventoryQ.data ?? [], [inventoryQ.data]);
  const forecast = useMemo(() => forecastQ.data?.points ?? [], [forecastQ.data]);
  const schedules = useMemo(() => schedulesQ.data ?? [], [schedulesQ.data]);
  const shipments = useMemo(() => shipmentsQ.data ?? [], [shipmentsQ.data]);
  const plans = useMemo(() => plansQ.data ?? [], [plansQ.data]);
  const usage = usageQ.data ?? null;
  const exceptionFeed = feedQ.data ?? null;
  const auditEvents = auditQ.data ?? [];
  const riskZones = useMemo(() => riskQ.data ?? [], [riskQ.data]);
  const appointments = appointmentsQ.data ?? [];

  // NB-29: milestone = 6 once m6 completes, else the sequential N-of-5.
  const activation = activationQ.data ?? null;
  const milestone = activation?.m6_completed ? 6 : (activation?.n_of_5 ?? 0);

  const isLoading =
    inventoryQ.isLoading ||
    forecastQ.isLoading ||
    schedulesQ.isLoading ||
    shipmentsQ.isLoading ||
    plansQ.isLoading ||
    feedQ.isLoading;

  const firstError =
    inventoryQ.error || forecastQ.error || schedulesQ.error ||
    shipmentsQ.error || plansQ.error || feedQ.error || auditQ.error ||
    riskQ.error || usageQ.error || appointmentsQ.error;

  const summary = useMemo(() => {
    const stock = inventory.reduce((sum, row) => sum + row.total_quantity_on_hand, 0);
    const safety = inventory.reduce((sum, row) => sum + row.total_safety_stock, 0);
    const avgUtil = inventory.length
      ? inventory.reduce((sum, row) => sum + row.utilization_percent, 0) / inventory.length
      : 0;
    const delayedShipments = shipments.filter((s) => s.status === 'delayed');
    const inTransitShipments = shipments.filter((s) => s.status === 'in_transit');
    const pendingPlans = plans.filter((p) => p.status === 'pending_approval');
    const forecastDemand = forecast.reduce((sum, point) => sum + point.predicted_demand, 0);
    const maxRiskScore = riskZones.length > 0 && schedules.length > 0
      ? Math.max(...riskZones.map((z) => z.severity_score))
      : 0;
    return {
      stock, safety,
      avgUtil: avgUtil.toFixed(1),
      delayedShipments, inTransitShipments,
      pendingPlans, forecastDemand,
      usagePercent: usage?.utilization_percent ?? null,
      maxRiskScore,
    };
  }, [forecast, inventory, plans, shipments, usage, riskZones, schedules]);

  async function handleRefresh() {
    setIsRefreshing(true);
    invalidateDashboard();
    setTimeout(() => setIsRefreshing(false), 800);
  }

  if (isLoading) return <DashboardSkeleton />;

  const feedSummary = exceptionFeed?.summary;
  const feedItems = exceptionFeed?.items ?? [];

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Control tower"
        title="Operations command surface"
        description="Monitor stock position, route status, open exceptions, approval pressure, and usage posture without leaving the operator frame."
        actions={
          <div className="flex flex-wrap items-center gap-2">
            {livePayload ? (
              <span className="inline-flex items-center gap-1.5 rounded-full border border-emerald-500/20 bg-emerald-950/30 px-3 py-2 text-xs font-medium uppercase tracking-wide text-emerald-200">
                <span className="inline-block h-1.5 w-1.5 rounded-full bg-emerald-400" />
                Live sync {new Date(livePayload.server_time).toLocaleTimeString()}
              </span>
            ) : null}
            <button
              onClick={handleRefresh}
              disabled={isRefreshing}
              className="glow-ring inline-flex min-h-10 items-center justify-center gap-2 rounded-full border border-slate-700 px-4 text-sm font-semibold text-slate-200 transition hover:border-slate-500 hover:bg-slate-900"
            >
              {isRefreshing ? (
                <svg className="h-4 w-4 animate-spin" viewBox="0 0 24 24" fill="none">
                  <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeDasharray="50 20" />
                </svg>
              ) : null}
              {isRefreshing ? 'Refreshing...' : 'Refresh data'}
            </button>
          </div>
        }
      />

      <ActivationBanner mode="compact" />

      {/* Layer C — two-tier metric hierarchy: the primary pair spans the
          framed primary strip; the secondary trio reads quieter on canvas. */}
      <div className="fp-shell-surface grid grid-cols-1 gap-4 p-5 sm:grid-cols-2">
        <MetricTile
          title="Open exceptions"
          value={feedSummary?.open_alerts ?? 0}
          detail={`${feedSummary?.delayed_shipments ?? summary.delayedShipments.length} delayed shipment${(feedSummary?.delayed_shipments ?? summary.delayedShipments.length) === 1 ? '' : 's'}.`}
          tone={(feedSummary?.open_alerts ?? 0) > 0 ? 'warning' : 'success'}
        />
        <MetricTile
          title="In-transit"
          value={summary.inTransitShipments.length}
          detail="Live movement across exception lanes."
          tone="info"
        />
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-3">
        {milestone >= gateMilestone('forecast-demand') ? (
          <MetricTile
            title="Forecast demand"
            value={summary.forecastDemand.toLocaleString()}
            detail="4-week projection horizon."
            tone="neutral"
          />
        ) : (
          <MetricTile
            title="Forecast demand"
            value="Locked"
            detail="Unlocks after Milestone 5."
            tone="neutral"
            cta={{ label: 'Continue onboarding', href: '/upload' }}
          />
        )}
        {milestone >= gateMilestone('weather-risk') ? (
          <MetricTile
            title="Simulated weather risk"
            value={summary.maxRiskScore > 0 ? `${summary.maxRiskScore}/10` : 'None'}
            detail="Deterministic simulation; not live weather data."
            tone={summary.maxRiskScore >= 8 ? 'danger' : summary.maxRiskScore >= 5 ? 'warning' : 'success'}
          />
        ) : (
          <MetricTile
            title="Simulated weather risk"
            value="Locked"
            detail="Unlocks after Milestone 5."
            tone="neutral"
            cta={{ label: 'Continue onboarding', href: '/upload' }}
          />
        )}
        <MetricTile
          title="Usage posture"
          value={summary.usagePercent == null ? 'N/A' : `${summary.usagePercent}%`}
          detail={summary.usagePercent == null ? 'Usage endpoint unavailable.' : 'Monthly task volume utilization.'}
          tone={summary.usagePercent != null && summary.usagePercent >= 100 ? 'danger' : summary.usagePercent != null && summary.usagePercent >= 80 ? 'warning' : 'success'}
        />
      </div>

      {firstError ? (
        <Panel className="border-rose-500/20 bg-rose-950/20">
          <p className="text-sm text-rose-200">
            Some data surfaces could not load. {(firstError as Error)?.message || 'Try refreshing.'}
          </p>
        </Panel>
      ) : null}

      <DecisionBriefPanel />

      <div className="grid grid-cols-1 gap-5 xl:grid-cols-[1.25fr_0.75fr]">
        <Panel
          eyebrow="Exception queue"
          title="What needs operator action"
          description="Unified feed: alerts, pending approvals, and route interventions."
        >
          <div className="divide-y divide-slate-800/60">
            {feedItems.slice(0, 6).map((item) => (
              <article
                key={`${item.source_type}:${item.source_id}`}
                className="py-3 transition-colors hover:bg-slate-900/40"
              >
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <div className="flex flex-wrap items-center gap-2">
                    <StatusBadge label={item.severity} tone={severityTone(item.severity)} />
                    <span className="text-xs uppercase tracking-wide text-slate-500">{item.source_type}</span>
                    <h3 className="font-['Space_Grotesk'] text-sm font-semibold text-slate-100">{item.title}</h3>
                  </div>
                  <span className="text-xs text-slate-500">{new Date(item.created_at).toLocaleString()}</span>
                </div>
                <p className="mt-1 text-sm leading-6 text-slate-400">{item.message}</p>
              </article>
            ))}
            {feedItems.length === 0 ? (
              <div className="rounded-[var(--fp-radius-panel)] border border-emerald-500/20 bg-emerald-950/20 p-5 text-center">
                <p className="font-['Space_Grotesk'] text-lg font-semibold text-emerald-200">Queue clear</p>
                <p className="mt-1 text-sm text-emerald-300/60">No open alerts requiring operator attention.</p>
              </div>
            ) : null}
          </div>
        </Panel>

        <div className="grid gap-5">
          <Panel eyebrow="Execution posture" title="Workspace readiness">
            <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-1 2xl:grid-cols-2">
              <div className="hover-lift fp-nested-surface p-3.5 transition">
                <p className="text-xs font-medium uppercase tracking-wide text-slate-500">Inventory position</p>
                <p className="mt-2.5 font-['Space_Grotesk'] text-2xl font-semibold tabular-nums text-slate-50">{summary.stock.toLocaleString()}</p>
                <p className="mt-1.5 text-sm text-slate-400">Safety stock: {summary.safety.toLocaleString()} units</p>
              </div>
              {milestone >= gateMilestone('utilization') ? (
                <div className="hover-lift fp-nested-surface p-3.5 transition">
                  <p className="text-xs font-medium uppercase tracking-wide text-slate-500">Utilization</p>
                  <p className="mt-2.5 font-['Space_Grotesk'] text-2xl font-semibold tabular-nums text-slate-50">{summary.avgUtil}%</p>
                  <p className="mt-1.5 text-sm text-slate-400">Average capacity pressure.</p>
                </div>
              ) : (
                <div className="rounded-[var(--fp-radius-panel)] border border-dashed border-slate-700/60 bg-slate-900/30 p-3.5">
                  <p className="text-xs font-medium uppercase tracking-wide text-slate-500">Utilization</p>
                  <p className="mt-2 text-sm text-slate-400">Unlocks after Milestone 4.</p>
                  <Link to="/upload" className="mt-2 inline-block text-sm font-semibold text-sky-300 underline-offset-4 hover:underline">
                    Continue onboarding →
                  </Link>
                </div>
              )}
              <div className="hover-lift fp-nested-surface p-3.5 transition">
                <p className="text-xs font-medium uppercase tracking-wide text-slate-500">Pending approvals</p>
                <p className="mt-2.5 font-['Space_Grotesk'] text-2xl font-semibold tabular-nums text-slate-50">{summary.pendingPlans.length}</p>
                <p className="mt-1.5 text-sm text-slate-400">Replenishment plans awaiting sign-off.</p>
              </div>
              <div className="hover-lift fp-nested-surface p-3.5 transition">
                <p className="text-xs font-medium uppercase tracking-wide text-slate-500">Route schedules</p>
                <p className="mt-2.5 font-['Space_Grotesk'] text-2xl font-semibold tabular-nums text-slate-50">{schedules.length}</p>
                <p className="mt-1.5 text-sm text-slate-400">Saved optimization output.</p>
              </div>
            </div>
          </Panel>

          <Panel eyebrow="Audit timeline" title="Latest workspace actions">
            <div className="space-y-3">
              {auditEvents.slice(0, 4).map((event) => (
                <article key={event.id} className="hover-lift fp-nested-surface p-4">
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <div>
                      <h3 className="font-['Space_Grotesk'] text-lg font-semibold text-slate-50">{event.description}</h3>
                      <p className="mt-1 text-sm text-slate-400">{event.event_type}</p>
                    </div>
                    <span className="text-xs text-slate-500">{new Date(event.created_at).toLocaleString()}</span>
                  </div>
                </article>
              ))}
              {auditEvents.length === 0 ? <p className="text-sm text-slate-400">No audit events yet.</p> : null}
            </div>
          </Panel>
        </div>
      </div>

      {milestone >= gateMilestone('dock-gantt') ? (
        <div className="grid grid-cols-1 gap-5 xl:grid-cols-2">
          <Panel eyebrow="Dock Management" title="Live Capacity Setup">
            <div className="h-[400px]">
              <DockGanttChart appointments={appointments} />
            </div>
          </Panel>
          <Panel eyebrow="Finance" title="Freight Invoice Reconciliation">
            <div className="h-[400px]">
              <FreightReconciliationPanel />
            </div>
          </Panel>
        </div>
      ) : null}

      <div className="grid grid-cols-1 gap-5 xl:grid-cols-3">
        <div className="xl:col-span-1">
          <FeedbackForm />
        </div>
        <div className="xl:col-span-2 space-y-5">
          {milestone >= gateMilestone('inventory-charts') ? (
            <InventoryCharts data={inventory} />
          ) : (
            <Panel eyebrow="Inventory" title="Stock position by warehouse">
              <GatePlaceholder milestone={gateMilestone('inventory-charts')} />
            </Panel>
          )}
          {milestone >= gateMilestone('forecast-chart') ? (
            <ForecastChart
              points={forecast}
              quality={forecastQ.data?.quality}
              modelName={forecastQ.data?.model_name}
            />
          ) : (
            <Panel eyebrow="Forecast" title="4-week demand projection">
              <GatePlaceholder milestone={gateMilestone('forecast-chart')} />
            </Panel>
          )}
        </div>
      </div>
    </div>
  );
}


import { useCallback, useEffect, useMemo, useState } from 'react';

import { ForecastChart } from '../components/ForecastChart';
import { InventoryCharts } from '../components/InventoryCharts';
import { MetricTile } from '../components/ui/MetricTile';
import { PageHeader } from '../components/ui/PageHeader';
import { Panel } from '../components/ui/Panel';
import { StatusBadge } from '../components/ui/StatusBadge';
import { useAuth } from '../context/AuthContext';
import { useLiveUpdates } from '../hooks/useLiveUpdates';
import { getCurrentUsage } from '../services/billingApi';
import {
  getForecast,
  getInventoryOverview,
  getRouteSchedules,
  listAlerts,
  listReplenishmentPlans,
  listShipments,
} from '../services/logisticsApi';
import type {
  Alert,
  ForecastPoint,
  InventoryOverviewRow,
  ReplenishmentPlan,
  RouteScheduleSummary,
  Shipment,
  UsageSummary,
} from '../types/api';

const POLL_INTERVAL_MS = 30000;

function severityTone(severity: Alert['severity']) {
  if (severity === 'critical') return 'danger';
  if (severity === 'high') return 'warning';
  if (severity === 'medium') return 'info';
  return 'neutral';
}

function scheduleTone(status: string) {
  if (status === 'completed' || status === 'delivered') return 'success';
  if (status === 'delayed' || status === 'failed') return 'danger';
  if (status === 'active' || status === 'in_progress') return 'warning';
  return 'neutral';
}

export function DashboardPage() {
  const { token } = useAuth();
  const [inventory, setInventory] = useState<InventoryOverviewRow[]>([]);
  const [forecast, setForecast] = useState<ForecastPoint[]>([]);
  const [schedules, setSchedules] = useState<RouteScheduleSummary[]>([]);
  const [shipments, setShipments] = useState<Shipment[]>([]);
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [plans, setPlans] = useState<ReplenishmentPlan[]>([]);
  const [usage, setUsage] = useState<UsageSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastLiveUpdate, setLastLiveUpdate] = useState<string | null>(null);

  const loadData = useCallback(async () => {
    try {
      setError(null);
      const [inventoryData, forecastData, scheduleData, shipmentData, alertData, planData, usageData] = await Promise.all([
        getInventoryOverview(),
        getForecast(4),
        getRouteSchedules(),
        listShipments(),
        listAlerts('open'),
        listReplenishmentPlans(),
        getCurrentUsage().catch(() => null),
      ]);
      setInventory(inventoryData);
      setForecast(forecastData.points);
      setSchedules(scheduleData);
      setShipments(shipmentData);
      setAlerts(alertData);
      setPlans(planData);
      setUsage(usageData);
    } catch (err: any) {
      setError(err?.response?.data?.detail || err.message || 'Failed to load dashboard data');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadData();
    const timer = setInterval(loadData, POLL_INTERVAL_MS);
    return () => clearInterval(timer);
  }, [loadData]);

  useLiveUpdates({
    token,
    onMessage: (payload) => {
      setInventory(payload.inventory_overview);
      setForecast(payload.forecast_preview);
      setSchedules(payload.route_summaries);
      setLastLiveUpdate(payload.server_time);
    },
  });

  const summary = useMemo(() => {
    const stock = inventory.reduce((sum, row) => sum + row.total_quantity_on_hand, 0);
    const safety = inventory.reduce((sum, row) => sum + row.total_safety_stock, 0);
    const avgUtil = inventory.length
      ? inventory.reduce((sum, row) => sum + row.utilization_percent, 0) / inventory.length
      : 0;
    const delayedShipments = shipments.filter((shipment) => shipment.status === 'delayed');
    const inTransitShipments = shipments.filter((shipment) => shipment.status === 'in_transit');
    const pendingPlans = plans.filter((plan) => plan.status === 'pending_approval');
    const forecastDemand = forecast.reduce((sum, point) => sum + point.predicted_demand, 0);
    return {
      stock,
      safety,
      avgUtil: avgUtil.toFixed(1),
      delayedShipments,
      inTransitShipments,
      pendingPlans,
      forecastDemand,
      usagePercent: usage?.utilization_percent ?? null,
    };
  }, [forecast, inventory, plans, shipments, usage]);

  const refreshButton = (
    <button
      onClick={loadData}
      className="inline-flex min-h-10 items-center justify-center rounded-full border border-slate-700 px-4 text-sm font-semibold text-slate-200 transition hover:border-slate-500 hover:bg-slate-900"
    >
      Refresh data
    </button>
  );

  if (loading) {
    return (
      <div className="space-y-5">
        <PageHeader
          eyebrow="Control tower"
          title="Operations command surface"
          description="Loading current route, shipment, exception, and planning signals for this workspace."
          actions={refreshButton}
        />
        <Panel>
          <p className="text-sm text-slate-400">Loading dashboard...</p>
        </Panel>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Control tower"
        title="Operations command surface"
        description="Monitor stock position, route status, open exceptions, approval pressure, and usage posture without leaving the operator frame."
        actions={
          <div className="flex flex-wrap items-center gap-2">
            {lastLiveUpdate ? (
              <span className="rounded-full border border-emerald-500/20 bg-emerald-950/30 px-3 py-2 text-xs font-semibold uppercase tracking-[0.18em] text-emerald-200">
                Live sync {new Date(lastLiveUpdate).toLocaleTimeString()}
              </span>
            ) : null}
            {refreshButton}
          </div>
        }
      />

      <div className="grid grid-cols-1 gap-4 xl:grid-cols-4">
        <MetricTile
          title="Open exceptions"
          value={alerts.length}
          detail={`${summary.delayedShipments.length} delayed shipment${summary.delayedShipments.length === 1 ? '' : 's'} currently compounding the queue.`}
          tone={alerts.length > 0 ? 'warning' : 'success'}
        />
        <MetricTile
          title="In-transit shipments"
          value={summary.inTransitShipments.length}
          detail="Track live movement and intervene on exception lanes before customer impact spreads."
          tone="info"
        />
        <MetricTile
          title="Forecast demand"
          value={summary.forecastDemand.toLocaleString()}
          detail="Projected demand volume aggregated from the current four-week forecast horizon."
          tone="neutral"
        />
        <MetricTile
          title="Usage posture"
          value={summary.usagePercent == null ? 'N/A' : `${summary.usagePercent}%`}
          detail={
            summary.usagePercent == null
              ? 'Usage endpoint unavailable for this workspace.'
              : 'Subscription utilization against the current included monthly task volume.'
          }
          tone={summary.usagePercent != null && summary.usagePercent >= 100 ? 'danger' : summary.usagePercent != null && summary.usagePercent >= 80 ? 'warning' : 'success'}
        />
      </div>

      {error ? (
        <Panel className="border-rose-500/25 bg-rose-950/12">
          <p className="text-sm text-rose-200">{error}</p>
        </Panel>
      ) : null}

      <div className="grid grid-cols-1 gap-5 xl:grid-cols-[1.15fr_0.85fr]">
        <Panel
          eyebrow="Exception queue"
          title="What needs operator action now"
          description="Open alerts and delayed shipments are the fastest path to avoidable cost when they sit unattended."
        >
          <div className="space-y-3">
            {alerts.slice(0, 4).map((alert) => (
              <article key={alert.id} className="rounded-[22px] border border-slate-800 bg-slate-900/70 p-4">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <div className="space-y-1">
                    <div className="flex flex-wrap items-center gap-2">
                      <StatusBadge label={alert.severity} tone={severityTone(alert.severity)} />
                      <span className="text-xs uppercase tracking-[0.18em] text-slate-500">{alert.alert_type}</span>
                    </div>
                    <h3 className="font-['Space_Grotesk'] text-lg font-semibold text-slate-50">{alert.title}</h3>
                  </div>
                  <span className="text-xs text-slate-500">{new Date(alert.created_at).toLocaleString()}</span>
                </div>
                <p className="mt-3 text-sm leading-6 text-slate-400">{alert.message}</p>
              </article>
            ))}

            {alerts.length === 0 ? (
              <div className="rounded-[22px] border border-emerald-500/20 bg-emerald-950/12 p-4 text-sm text-emerald-200">
                No open alerts. The queue is currently clear.
              </div>
            ) : null}

            {summary.delayedShipments.slice(0, 3).map((shipment) => (
              <article key={shipment.id} className="rounded-[22px] border border-amber-500/20 bg-amber-950/10 p-4">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <div>
                    <p className="text-xs font-semibold uppercase tracking-[0.18em] text-amber-200/80">Delayed shipment</p>
                    <h3 className="mt-1 font-['Space_Grotesk'] text-lg font-semibold text-slate-50">{shipment.shipment_no}</h3>
                  </div>
                  <StatusBadge label={shipment.status} tone="warning" />
                </div>
                <p className="mt-3 text-sm leading-6 text-slate-400">
                  {shipment.origin_warehouse_code} to {shipment.destination_warehouse_code}
                  {shipment.delay_reason ? ` - ${shipment.delay_reason}` : ''}
                </p>
              </article>
            ))}
          </div>
        </Panel>

        <div className="grid gap-5">
          <Panel
            eyebrow="Execution posture"
            title="Workspace readiness and commercial signals"
            description="Keep approval load, capacity posture, and plan usage visible while the team is dispatching."
          >
            <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-1 2xl:grid-cols-2">
              <div className="rounded-[22px] border border-slate-800 bg-slate-900/70 p-4">
                <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">Inventory position</p>
                <p className="mt-3 font-['Space_Grotesk'] text-3xl font-semibold text-slate-50">{summary.stock.toLocaleString()}</p>
                <p className="mt-2 text-sm text-slate-400">Safety stock total: {summary.safety.toLocaleString()} units</p>
              </div>
              <div className="rounded-[22px] border border-slate-800 bg-slate-900/70 p-4">
                <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">Warehouse utilization</p>
                <p className="mt-3 font-['Space_Grotesk'] text-3xl font-semibold text-slate-50">{summary.avgUtil}%</p>
                <p className="mt-2 text-sm text-slate-400">Average capacity pressure across tracked warehouse locations.</p>
              </div>
              <div className="rounded-[22px] border border-slate-800 bg-slate-900/70 p-4">
                <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">Pending approvals</p>
                <p className="mt-3 font-['Space_Grotesk'] text-3xl font-semibold text-slate-50">{summary.pendingPlans.length}</p>
                <p className="mt-2 text-sm text-slate-400">Replenishment plans waiting for admin sign-off.</p>
              </div>
              <div className="rounded-[22px] border border-slate-800 bg-slate-900/70 p-4">
                <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">Saved route schedules</p>
                <p className="mt-3 font-['Space_Grotesk'] text-3xl font-semibold text-slate-50">{schedules.length}</p>
                <p className="mt-2 text-sm text-slate-400">Optimization output currently saved in the route schedule store.</p>
              </div>
            </div>
          </Panel>

          <Panel
            eyebrow="Route snapshot"
            title="Latest saved route schedules"
            description="A quick read on the most recent route assets before drilling into the Route Studio."
          >
            <div className="space-y-3">
              {schedules.slice(0, 4).map((schedule) => (
                <article key={schedule.id} className="rounded-[22px] border border-slate-800 bg-slate-900/70 p-4">
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <div>
                      <h3 className="font-['Space_Grotesk'] text-lg font-semibold text-slate-50">{schedule.route_name}</h3>
                      <p className="mt-1 text-sm text-slate-400">{schedule.schedule_date}</p>
                    </div>
                    <StatusBadge label={schedule.status} tone={scheduleTone(schedule.status)} />
                  </div>
                  <div className="mt-3 grid gap-2 text-sm text-slate-400 sm:grid-cols-3">
                    <span>{schedule.total_distance_km} km</span>
                    <span>${schedule.total_cost}</span>
                    <span>{schedule.estimated_duration_min} min</span>
                  </div>
                </article>
              ))}

              {schedules.length === 0 ? <p className="text-sm text-slate-400">No saved route schedules yet.</p> : null}
            </div>
          </Panel>
        </div>
      </div>

      <InventoryCharts data={inventory} />
      <ForecastChart points={forecast} />
    </div>
  );
}

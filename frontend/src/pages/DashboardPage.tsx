import { useCallback, useEffect, useMemo, useState } from 'react';

import { ForecastChart } from '../components/ForecastChart';
import { InventoryCharts } from '../components/InventoryCharts';
import { StatCard } from '../components/StatCard';
import { useAuth } from '../context/AuthContext';
import { useLiveUpdates } from '../hooks/useLiveUpdates';
import { getForecast, getInventoryOverview } from '../services/logisticsApi';
import type { ForecastPoint, InventoryOverviewRow } from '../types/api';

const POLL_INTERVAL_MS = 30000;

export function DashboardPage() {
  const { token } = useAuth();
  const [inventory, setInventory] = useState<InventoryOverviewRow[]>([]);
  const [forecast, setForecast] = useState<ForecastPoint[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastLiveUpdate, setLastLiveUpdate] = useState<string | null>(null);

  const loadData = useCallback(async () => {
    try {
      setError(null);
      const [inventoryData, forecastData] = await Promise.all([getInventoryOverview(), getForecast(4)]);
      setInventory(inventoryData);
      setForecast(forecastData.points);
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
      setLastLiveUpdate(payload.server_time);
    },
  });

  const totals = useMemo(() => {
    const stock = inventory.reduce((sum, row) => sum + row.total_quantity_on_hand, 0);
    const safety = inventory.reduce((sum, row) => sum + row.total_safety_stock, 0);
    const avgUtil = inventory.length
      ? inventory.reduce((sum, row) => sum + row.utilization_percent, 0) / inventory.length
      : 0;
    return { stock, safety, avgUtil: avgUtil.toFixed(2) };
  }, [inventory]);

  if (loading) return <p className="text-slate-600">Loading dashboard...</p>;

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        <StatCard title="Total Stock" value={totals.stock} />
        <StatCard title="Total Safety Stock" value={totals.safety} />
        <StatCard title="Average Utilization" value={`${totals.avgUtil}%`} subtitle="Across warehouses" />
      </div>

      {lastLiveUpdate ? (
        <p className="text-xs text-emerald-700">Live update synced at {new Date(lastLiveUpdate).toLocaleTimeString()}</p>
      ) : null}

      {error ? <p className="text-red-600">{error}</p> : null}

      <InventoryCharts data={inventory} />
      <ForecastChart points={forecast} />
    </div>
  );
}

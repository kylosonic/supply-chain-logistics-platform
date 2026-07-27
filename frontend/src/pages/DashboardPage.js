import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { useEffect, useMemo, useState } from 'react';
import { ForecastChart } from '../components/ForecastChart';
import { InventoryCharts } from '../components/InventoryCharts';
import { StatCard } from '../components/StatCard';
import { getForecast, getInventoryOverview } from '../services/logisticsApi';
const POLL_INTERVAL_MS = 30000;
export function DashboardPage() {
    const [inventory, setInventory] = useState([]);
    const [forecast, setForecast] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    async function loadData() {
        try {
            setError(null);
            const [inventoryData, forecastData] = await Promise.all([getInventoryOverview(), getForecast(4)]);
            setInventory(inventoryData);
            setForecast(forecastData.points);
        }
        catch (err) {
            setError(err?.response?.data?.detail || err.message || 'Failed to load dashboard data');
        }
        finally {
            setLoading(false);
        }
    }
    useEffect(() => {
        loadData();
        const timer = setInterval(loadData, POLL_INTERVAL_MS);
        return () => clearInterval(timer);
    }, []);
    const totals = useMemo(() => {
        const stock = inventory.reduce((sum, row) => sum + row.total_quantity_on_hand, 0);
        const safety = inventory.reduce((sum, row) => sum + row.total_safety_stock, 0);
        const avgUtil = inventory.length
            ? inventory.reduce((sum, row) => sum + row.utilization_percent, 0) / inventory.length
            : 0;
        return { stock, safety, avgUtil: avgUtil.toFixed(2) };
    }, [inventory]);
    if (loading)
        return _jsx("p", { className: "text-slate-600", children: "Loading dashboard..." });
    return (_jsxs("div", { className: "space-y-6", children: [_jsxs("div", { className: "grid grid-cols-1 gap-4 sm:grid-cols-3", children: [_jsx(StatCard, { title: "Total Stock", value: totals.stock }), _jsx(StatCard, { title: "Total Safety Stock", value: totals.safety }), _jsx(StatCard, { title: "Average Utilization", value: `${totals.avgUtil}%`, subtitle: "Across warehouses" })] }), error ? _jsx("p", { className: "text-red-600", children: error }) : null, _jsx(InventoryCharts, { data: inventory }), _jsx(ForecastChart, { points: forecast })] }));
}

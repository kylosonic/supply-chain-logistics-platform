import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { useEffect, useState } from 'react';
import { RouteOptimizerForm } from '../components/RouteOptimizerForm';
import { RouteSchedulesTable } from '../components/RouteSchedulesTable';
import { getRouteSchedules } from '../services/logisticsApi';
export function RoutesPage() {
    const [schedules, setSchedules] = useState([]);
    const [error, setError] = useState(null);
    async function loadSchedules() {
        try {
            setError(null);
            const data = await getRouteSchedules();
            setSchedules(data);
        }
        catch (err) {
            setError(err?.response?.data?.detail || err.message || 'Failed to load route schedules');
        }
    }
    useEffect(() => {
        loadSchedules();
    }, []);
    return (_jsxs("div", { className: "space-y-6", children: [_jsx(RouteOptimizerForm, {}), _jsxs("div", { className: "flex items-center justify-between", children: [_jsx("h2", { className: "text-sm font-semibold text-slate-700", children: "Saved Route Schedules" }), _jsx("button", { onClick: loadSchedules, className: "rounded bg-slate-800 px-3 py-2 text-xs text-white", children: "Refresh" })] }), error ? _jsx("p", { className: "text-red-600", children: error }) : null, _jsx(RouteSchedulesTable, { schedules: schedules })] }));
}

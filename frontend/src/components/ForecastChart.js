import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { CartesianGrid, Legend, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis, } from 'recharts';
export function ForecastChart({ points }) {
    const grouped = new Map();
    points.forEach((point) => {
        const key = point.week_start;
        grouped.set(key, (grouped.get(key) ?? 0) + point.predicted_demand);
    });
    const data = Array.from(grouped.entries())
        .map(([week_start, predicted_total_demand]) => ({ week_start, predicted_total_demand }))
        .sort((a, b) => a.week_start.localeCompare(b.week_start));
    return (_jsxs("div", { className: "rounded-xl bg-white p-4 shadow-sm ring-1 ring-slate-200", children: [_jsx("h3", { className: "mb-4 text-sm font-semibold text-slate-700", children: "Predicted Weekly Demand (Aggregated)" }), _jsx("div", { className: "h-80", children: _jsx(ResponsiveContainer, { width: "100%", height: "100%", children: _jsxs(LineChart, { data: data, children: [_jsx(CartesianGrid, { strokeDasharray: "3 3" }), _jsx(XAxis, { dataKey: "week_start" }), _jsx(YAxis, {}), _jsx(Tooltip, {}), _jsx(Legend, {}), _jsx(Line, { type: "monotone", dataKey: "predicted_total_demand", stroke: "#ef4444", strokeWidth: 3, dot: false })] }) }) })] }));
}

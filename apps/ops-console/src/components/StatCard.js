import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
export function StatCard({ title, value, subtitle }) {
    return (_jsxs("div", { className: "rounded-xl bg-white p-4 shadow-sm ring-1 ring-slate-200", children: [_jsx("p", { className: "text-sm text-slate-600", children: title }), _jsx("p", { className: "mt-2 text-2xl font-semibold text-slate-900", children: value }), subtitle ? _jsx("p", { className: "mt-1 text-xs text-slate-500", children: subtitle }) : null] }));
}

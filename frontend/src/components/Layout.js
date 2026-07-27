import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { Link, NavLink } from 'react-router-dom';
const navItems = [
    { to: '/', label: 'Dashboard' },
    { to: '/routes', label: 'Routes' },
    { to: '/upload', label: 'CSV Upload' },
];
export function Layout({ children }) {
    return (_jsxs("div", { className: "min-h-screen bg-slate-100", children: [_jsx("header", { className: "border-b border-slate-200 bg-white", children: _jsxs("div", { className: "mx-auto flex max-w-7xl items-center justify-between px-4 py-4 sm:px-6 lg:px-8", children: [_jsx(Link, { to: "/", className: "text-lg font-semibold text-slate-900", children: "Supply Chain Logistics Platform" }), _jsx("nav", { className: "flex gap-2", children: navItems.map((item) => (_jsx(NavLink, { to: item.to, className: ({ isActive }) => `rounded-md px-3 py-2 text-sm font-medium ${isActive ? 'bg-slate-900 text-white' : 'text-slate-700 hover:bg-slate-200'}`, children: item.label }, item.to))) })] }) }), _jsx("main", { className: "mx-auto max-w-7xl px-4 py-6 sm:px-6 lg:px-8", children: children })] }));
}

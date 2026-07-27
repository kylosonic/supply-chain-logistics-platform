import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { useState } from 'react';
import { uploadInventoryCsv, uploadOrdersCsv } from '../services/logisticsApi';
export function CsvUploadPanel() {
    const [inventoryFile, setInventoryFile] = useState(null);
    const [ordersFile, setOrdersFile] = useState(null);
    const [result, setResult] = useState('');
    const [isUploading, setIsUploading] = useState(false);
    async function submitInventory() {
        if (!inventoryFile)
            return;
        setIsUploading(true);
        try {
            const response = await uploadInventoryCsv(inventoryFile);
            setResult(`Inventory import: processed=${response.records_processed}, created=${response.records_created}, updated=${response.records_updated}, errors=${response.errors.length}`);
        }
        catch (err) {
            setResult(`Inventory import failed: ${err?.response?.data?.detail || err.message}`);
        }
        finally {
            setIsUploading(false);
        }
    }
    async function submitOrders() {
        if (!ordersFile)
            return;
        setIsUploading(true);
        try {
            const response = await uploadOrdersCsv(ordersFile);
            setResult(`Orders import: processed=${response.records_processed}, created=${response.records_created}, errors=${response.errors.length}`);
        }
        catch (err) {
            setResult(`Orders import failed: ${err?.response?.data?.detail || err.message}`);
        }
        finally {
            setIsUploading(false);
        }
    }
    return (_jsxs("div", { className: "space-y-6", children: [_jsxs("div", { className: "rounded-xl bg-white p-4 shadow-sm ring-1 ring-slate-200", children: [_jsx("h3", { className: "mb-3 text-sm font-semibold text-slate-700", children: "Upload Inventory CSV" }), _jsx("input", { type: "file", accept: ".csv", onChange: (e) => setInventoryFile(e.target.files?.[0] || null) }), _jsx("button", { disabled: !inventoryFile || isUploading, onClick: submitInventory, className: "ml-3 rounded bg-slate-900 px-3 py-2 text-sm text-white", children: "Upload Inventory" })] }), _jsxs("div", { className: "rounded-xl bg-white p-4 shadow-sm ring-1 ring-slate-200", children: [_jsx("h3", { className: "mb-3 text-sm font-semibold text-slate-700", children: "Upload Orders CSV" }), _jsx("input", { type: "file", accept: ".csv", onChange: (e) => setOrdersFile(e.target.files?.[0] || null) }), _jsx("button", { disabled: !ordersFile || isUploading, onClick: submitOrders, className: "ml-3 rounded bg-slate-900 px-3 py-2 text-sm text-white", children: "Upload Orders" })] }), result ? _jsx("p", { className: "text-sm text-slate-700", children: result }) : null] }));
}

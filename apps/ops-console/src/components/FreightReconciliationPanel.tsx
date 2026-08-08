import { useEffect, useState, useRef } from 'react';
import type { FreightInvoice } from '../services/logisticsApi';
import { getInvoices, uploadInvoices } from '../services/logisticsApi';

export function FreightReconciliationPanel() {
  const [invoices, setInvoices] = useState<FreightInvoice[]>([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const fetchInvoices = async () => {
    try {
      const data = await getInvoices();
      setInvoices(data);
    } catch (err) {
      console.error('Failed to fetch invoices', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchInvoices();
  }, []);

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setUploading(true);
    try {
      await uploadInvoices(file);
      await fetchInvoices();
    } catch (err) {
      console.error('Failed to upload invoices', err);
      alert('Upload failed. Please check the CSV format.');
    } finally {
      setUploading(false);
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    }
  };

  const mismatches = invoices.filter((inv) => inv.status === 'mismatch_flagged');
  const totalVariance = mismatches.reduce((acc, curr) => acc + curr.variance, 0);

  return (
    <div className="flex h-full flex-col">
      <div className="mb-4 flex items-center justify-between">
        <h3 className="text-sm font-semibold text-slate-100">Freight Invoice Reconciliation</h3>
        <div>
          <input
            type="file"
            accept=".csv"
            className="hidden"
            ref={fileInputRef}
            onChange={handleFileUpload}
          />
          <button
            className="rounded bg-sky-500 px-3 py-1 text-xs font-medium text-slate-950 hover:bg-sky-400 disabled:opacity-50"
            onClick={() => fileInputRef.current?.click()}
            disabled={uploading}
          >
            {uploading ? 'Uploading...' : 'Upload Invoices'}
          </button>
        </div>
      </div>

      <div className="flex gap-4 mb-4">
        <div className="flex-1 fp-nested-surface p-3">
          <div className="text-xs text-slate-500">Flagged Mismatches</div>
          <div className="font-mono text-2xl font-bold tabular-nums text-amber-400">{mismatches.length}</div>
        </div>
        <div className="flex-1 fp-nested-surface p-3">
          <div className="text-xs text-slate-500">Total Variance Cost</div>
          <div className="font-mono text-2xl font-bold tabular-nums text-red-500">${totalVariance.toFixed(2)}</div>
        </div>
      </div>

      <div className="flex-1 overflow-auto fp-nested-surface">
        {loading ? (
          <div className="flex h-full items-center justify-center p-4">Loading...</div>
        ) : (
          <table className="w-full text-left text-sm text-slate-400">
            <thead className="sticky top-0 bg-slate-900 text-xs font-medium text-slate-300">
              <tr>
                <th className="px-4 py-3">Carrier</th>
                <th className="px-4 py-3">Order ID</th>
                <th className="px-4 py-3">Quoted ($)</th>
                <th className="px-4 py-3">Actual ($)</th>
                <th className="px-4 py-3">Variance ($)</th>
                <th className="px-4 py-3">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {invoices.length === 0 ? (
                <tr>
                  <td colSpan={6} className="px-4 py-4 text-center">No invoices uploaded</td>
                </tr>
              ) : (
                invoices.map((inv) => (
                  <tr key={inv.id} className="hover:bg-slate-800/40">
                    <td className="px-4 py-3 font-medium text-slate-100">{inv.carrier_id}</td>
                    <td className="px-4 py-3 font-mono text-xs">{inv.order_id.slice(0, 8)}...</td>
                    <td className="px-4 py-3 font-mono tabular-nums">{inv.quoted_rate.toFixed(2)}</td>
                    <td className="px-4 py-3 font-mono tabular-nums">{inv.actual_rate.toFixed(2)}</td>
                    <td className="px-4 py-3">
                      <span className={`font-mono tabular-nums ${inv.variance > 0 ? 'text-red-500' : 'text-green-500'}`}>
                        {inv.variance > 0 ? '+' : ''}{inv.variance.toFixed(2)}
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      <span
                        className={`inline-flex rounded-full px-2 py-0.5 text-[10px] font-semibold ${
                          inv.status === 'mismatch_flagged'
                            ? 'bg-amber-900/30 text-amber-400'
                            : 'bg-green-900/30 text-green-400'
                        }`}
                      >
                        {inv.status === 'mismatch_flagged' ? 'Mismatch' : 'Matched'}
                      </span>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}

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
        <h3 className="text-sm font-semibold text-neutral-900 dark:text-neutral-100">Freight Invoice Reconciliation</h3>
        <div>
          <input
            type="file"
            accept=".csv"
            className="hidden"
            ref={fileInputRef}
            onChange={handleFileUpload}
          />
          <button
            className="rounded bg-blue-600 px-3 py-1 text-xs font-medium text-white hover:bg-blue-700 disabled:opacity-50"
            onClick={() => fileInputRef.current?.click()}
            disabled={uploading}
          >
            {uploading ? 'Uploading...' : 'Upload Invoices'}
          </button>
        </div>
      </div>

      <div className="flex gap-4 mb-4">
        <div className="flex-1 rounded-lg bg-neutral-100 p-3 dark:bg-neutral-800">
          <div className="text-xs text-neutral-500">Flagged Mismatches</div>
          <div className="text-2xl font-bold text-orange-500">{mismatches.length}</div>
        </div>
        <div className="flex-1 rounded-lg bg-neutral-100 p-3 dark:bg-neutral-800">
          <div className="text-xs text-neutral-500">Total Variance Cost</div>
          <div className="text-2xl font-bold text-red-500">${totalVariance.toFixed(2)}</div>
        </div>
      </div>

      <div className="flex-1 overflow-auto rounded-xl bg-neutral-100 dark:bg-neutral-800">
        {loading ? (
          <div className="flex h-full items-center justify-center p-4">Loading...</div>
        ) : (
          <table className="w-full text-left text-sm text-neutral-600 dark:text-neutral-400">
            <thead className="sticky top-0 bg-neutral-200 text-xs font-medium text-neutral-700 dark:bg-neutral-900 dark:text-neutral-300">
              <tr>
                <th className="px-4 py-3">Carrier</th>
                <th className="px-4 py-3">Order ID</th>
                <th className="px-4 py-3">Quoted ($)</th>
                <th className="px-4 py-3">Actual ($)</th>
                <th className="px-4 py-3">Variance ($)</th>
                <th className="px-4 py-3">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-neutral-200 dark:divide-neutral-700">
              {invoices.length === 0 ? (
                <tr>
                  <td colSpan={6} className="px-4 py-4 text-center">No invoices uploaded</td>
                </tr>
              ) : (
                invoices.map((inv) => (
                  <tr key={inv.id} className="hover:bg-neutral-200/50 dark:hover:bg-neutral-700/50">
                    <td className="px-4 py-3 font-medium text-neutral-900 dark:text-neutral-100">{inv.carrier_id}</td>
                    <td className="px-4 py-3 font-mono text-xs">{inv.order_id.slice(0, 8)}...</td>
                    <td className="px-4 py-3">{inv.quoted_rate.toFixed(2)}</td>
                    <td className="px-4 py-3">{inv.actual_rate.toFixed(2)}</td>
                    <td className="px-4 py-3">
                      <span className={inv.variance > 0 ? 'text-red-500' : 'text-green-500'}>
                        {inv.variance > 0 ? '+' : ''}{inv.variance.toFixed(2)}
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      <span
                        className={`inline-flex rounded-full px-2 py-0.5 text-[10px] font-semibold ${
                          inv.status === 'mismatch_flagged'
                            ? 'bg-orange-100 text-orange-800 dark:bg-orange-900/30 dark:text-orange-400'
                            : 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400'
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

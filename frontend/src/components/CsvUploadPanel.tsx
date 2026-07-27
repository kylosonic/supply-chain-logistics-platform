import { useState } from 'react';

import { uploadInventoryCsv, uploadOrdersCsv } from '../services/logisticsApi';

export function CsvUploadPanel() {
  const [inventoryFile, setInventoryFile] = useState<File | null>(null);
  const [ordersFile, setOrdersFile] = useState<File | null>(null);
  const [result, setResult] = useState<string>('');
  const [isUploading, setIsUploading] = useState(false);

  async function submitInventory() {
    if (!inventoryFile) return;
    setIsUploading(true);
    try {
      const response = await uploadInventoryCsv(inventoryFile);
      setResult(`Inventory import: processed=${response.records_processed}, created=${response.records_created}, updated=${response.records_updated}, errors=${response.errors.length}`);
    } catch (err: any) {
      setResult(`Inventory import failed: ${err?.response?.data?.detail || err.message}`);
    } finally {
      setIsUploading(false);
    }
  }

  async function submitOrders() {
    if (!ordersFile) return;
    setIsUploading(true);
    try {
      const response = await uploadOrdersCsv(ordersFile);
      setResult(`Orders import: processed=${response.records_processed}, created=${response.records_created}, errors=${response.errors.length}`);
    } catch (err: any) {
      setResult(`Orders import failed: ${err?.response?.data?.detail || err.message}`);
    } finally {
      setIsUploading(false);
    }
  }

  return (
    <div className="space-y-6">
      <div className="rounded-xl bg-white p-4 shadow-sm ring-1 ring-slate-200">
        <h3 className="mb-3 text-sm font-semibold text-slate-700">Upload Inventory CSV</h3>
        <input type="file" accept=".csv" onChange={(e) => setInventoryFile(e.target.files?.[0] || null)} />
        <button disabled={!inventoryFile || isUploading} onClick={submitInventory} className="ml-3 rounded bg-slate-900 px-3 py-2 text-sm text-white">
          Upload Inventory
        </button>
      </div>

      <div className="rounded-xl bg-white p-4 shadow-sm ring-1 ring-slate-200">
        <h3 className="mb-3 text-sm font-semibold text-slate-700">Upload Orders CSV</h3>
        <input type="file" accept=".csv" onChange={(e) => setOrdersFile(e.target.files?.[0] || null)} />
        <button disabled={!ordersFile || isUploading} onClick={submitOrders} className="ml-3 rounded bg-slate-900 px-3 py-2 text-sm text-white">
          Upload Orders
        </button>
      </div>

      {result ? <p className="text-sm text-slate-700">{result}</p> : null}
    </div>
  );
}

import { useState } from 'react';

import {
  uploadFleetAssetsCsv,
  uploadInventoryCsv,
  uploadItemsCsv,
  uploadOrdersCsv,
  uploadWarehousesCsv,
} from '../services/logisticsApi';

type UploadKind = 'warehouses' | 'items' | 'fleet' | 'inventory' | 'orders';

type UploadSpec = {
  key: UploadKind;
  title: string;
  hint: string;
  actionLabel: string;
};

const uploadSpecs: UploadSpec[] = [
  {
    key: 'warehouses',
    title: 'Upload Warehouses CSV',
    hint: 'Columns: code,name,address,city,state,country,latitude,longitude,capacity_units',
    actionLabel: 'Upload Warehouses',
  },
  {
    key: 'items',
    title: 'Upload Items CSV',
    hint: 'Columns: sku,name,category,unit_cost,reorder_level',
    actionLabel: 'Upload Items',
  },
  {
    key: 'fleet',
    title: 'Upload Fleet Assets CSV (Cars + Drivers)',
    hint: 'Columns: vehicle_code,driver_name,capacity_units (+ optional driver_contact,status)',
    actionLabel: 'Upload Fleet Assets',
  },
  {
    key: 'inventory',
    title: 'Upload Inventory CSV',
    hint: 'Columns: warehouse_code,sku,quantity_on_hand (+ optional safety_stock)',
    actionLabel: 'Upload Inventory',
  },
  {
    key: 'orders',
    title: 'Upload Orders CSV',
    hint: 'Columns: order_date,warehouse_code,sku,quantity (+ optional unit_price,customer_region)',
    actionLabel: 'Upload Orders',
  },
];

export function CsvUploadPanel() {
  const [files, setFiles] = useState<Record<UploadKind, File | null>>({
    warehouses: null,
    items: null,
    fleet: null,
    inventory: null,
    orders: null,
  });
  const [result, setResult] = useState<string>('');
  const [isUploading, setIsUploading] = useState(false);

  async function submit(kind: UploadKind) {
    const file = files[kind];
    if (!file) return;

    setIsUploading(true);
    try {
      const response =
        kind === 'warehouses'
          ? await uploadWarehousesCsv(file)
          : kind === 'items'
            ? await uploadItemsCsv(file)
            : kind === 'fleet'
              ? await uploadFleetAssetsCsv(file)
              : kind === 'inventory'
                ? await uploadInventoryCsv(file)
                : await uploadOrdersCsv(file);

      setResult(
        `${kind} import: processed=${response.records_processed}, created=${response.records_created}, updated=${response.records_updated}, errors=${response.errors.length}`,
      );
    } catch (err: any) {
      setResult(`${kind} import failed: ${err?.response?.data?.detail || err.message}`);
    } finally {
      setIsUploading(false);
    }
  }

  return (
    <div className="space-y-6">
      {uploadSpecs.map((spec) => (
        <div key={spec.key} className="rounded-xl bg-white p-4 shadow-sm ring-1 ring-slate-200">
          <h3 className="mb-1 text-sm font-semibold text-slate-700">{spec.title}</h3>
          <p className="mb-3 text-xs text-slate-500">{spec.hint}</p>
          <input
            type="file"
            accept=".csv"
            onChange={(event) =>
              setFiles((prev) => ({
                ...prev,
                [spec.key]: event.target.files?.[0] || null,
              }))
            }
          />
          <button
            disabled={!files[spec.key] || isUploading}
            onClick={() => submit(spec.key)}
            className="ml-3 rounded bg-slate-900 px-3 py-2 text-sm text-white"
          >
            {spec.actionLabel}
          </button>
        </div>
      ))}

      {result ? <p className="text-sm text-slate-700">{result}</p> : null}
    </div>
  );
}

import { useState } from 'react';
import { useQueryClient } from '@tanstack/react-query';

import { useActivationState } from '../hooks/queries';
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
  const [results, setResults] = useState<Partial<Record<UploadKind, string>>>({});
  const [activeKind, setActiveKind] = useState<UploadKind | null>(null);
  const queryClient = useQueryClient();
  const activationQ = useActivationState();
  const freeCapLocked = activationQ.data?.free_cap?.locked ?? false;

  async function submit(kind: UploadKind) {
    const file = files[kind];
    if (!file) return;

    setActiveKind(kind);
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

        setResults((prev) => ({
          ...prev,
          [kind]: `${kind} import: processed=${response.records_processed}, created=${response.records_created}, updated=${response.records_updated}, errors=${response.errors.length}`,
        }));
        // NB-30.4: milestone state reflects without a page reload.
        queryClient.invalidateQueries({ queryKey: ['activation'] });
    } catch (err: any) {
        setResults((prev) => ({
          ...prev,
          [kind]: `${kind} import failed: ${err?.response?.data?.detail || err.message}`,
        }));
    } finally {
        setActiveKind(null);
    }
  }

    const fieldClassName =
      'min-h-11 rounded-2xl border border-slate-700 bg-slate-900/80 px-4 text-sm text-slate-100 outline-none transition file:mr-3 file:rounded-full file:border-0 file:bg-sky-400/15 file:px-3 file:py-2 file:text-sm file:font-semibold file:text-sky-200 hover:file:bg-sky-400/20';

  return (
      <div className="grid grid-cols-1 gap-4 xl:grid-cols-2">
        {uploadSpecs.map((spec, index) => (
          <article key={spec.key} className="animate-fade-in hover-lift rounded-[26px] border border-slate-800/80 bg-slate-950/72 p-5 shadow-[0_24px_80px_rgba(2,12,20,0.28)] transition" style={{ animationDelay: `${index * 0.06}s` }}>
            <div className="flex items-start justify-between gap-3">
              <div>
                <p className="text-xs font-semibold uppercase tracking-[0.18em] text-sky-300/80">Step {index + 1}</p>
                <h3 className="mt-2 font-['Space_Grotesk'] text-xl font-semibold text-slate-50">{spec.title}</h3>
              </div>
              <span className="rounded-full border border-slate-700 px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.18em] text-slate-300">
                {spec.key}
              </span>
            </div>

            <p className="mt-3 text-sm leading-6 text-slate-400">{spec.hint}</p>

            <div className="mt-4 space-y-3">
              <input
                className={fieldClassName}
                type="file"
                accept=".csv"
                onChange={(event) =>
                  setFiles((prev) => ({
                    ...prev,
                    [spec.key]: event.target.files?.[0] || null,
                  }))
                }
              />
              <div className="flex flex-wrap items-center gap-3">
                <button
                  disabled={!files[spec.key] || activeKind !== null || freeCapLocked}
                  onClick={() => submit(spec.key)}
                  className="glow-ring inline-flex min-h-11 items-center justify-center gap-2 rounded-full bg-gradient-to-r from-sky-300 via-sky-400 to-teal-300 px-4 text-sm font-semibold text-slate-950 transition hover:brightness-105 disabled:cursor-not-allowed disabled:opacity-60"
                >
                  {activeKind === spec.key ? 'Uploading...' : freeCapLocked ? 'Writes locked (Free cap)' : spec.actionLabel}
                </button>
                <span className="text-sm text-slate-500">{files[spec.key]?.name || 'No file selected'}</span>
              </div>
            </div>

            {results[spec.key] ? <p className="mt-4 text-sm text-slate-300">{results[spec.key]}</p> : null}
          </article>
        ))}
    </div>
  );
}

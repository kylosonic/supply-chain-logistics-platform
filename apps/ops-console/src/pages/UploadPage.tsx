import { ActivationBanner } from '../components/ActivationBanner';
import { CsvUploadPanel } from '../components/CsvUploadPanel';
import { PageHeader } from '../components/ui/PageHeader';
import { Panel } from '../components/ui/Panel';

export function UploadPage() {
  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Data intake"
        title="Load a workspace in the right operational order"
        description="Bring warehouses, items, fleet assets, inventory, and orders into the system in sequence so routing, forecasting, and exception logic have a stable base."
      />

      <ActivationBanner mode="checklist" />

      <Panel
        eyebrow="Import sequence"
        title="Recommended onboarding order"
        description="Follow the steps top to bottom so downstream files can resolve against upstream warehouse, SKU, and fleet references."
      >
        <div className="grid gap-3 text-sm text-slate-300 md:grid-cols-5">
          {['Warehouses', 'Items', 'Fleet', 'Inventory', 'Orders'].map((step, index) => (
            <div key={step} className="rounded-[20px] border border-slate-800 bg-slate-900/70 px-4 py-4">
              <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">Step {index + 1}</p>
              <p className="mt-2 font-['Space_Grotesk'] text-lg font-semibold text-slate-50">{step}</p>
            </div>
          ))}
        </div>
      </Panel>

      <CsvUploadPanel />
    </div>
  );
}

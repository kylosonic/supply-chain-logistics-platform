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
        <ol className="flex flex-wrap items-center gap-2.5">
          {['Warehouses', 'Items', 'Fleet', 'Inventory', 'Orders'].map((step, index) => (
            <li key={step} className="fp-pill">
              <span className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">Step {index + 1}</span>
              <span className="font-['Space_Grotesk'] text-sm font-semibold text-slate-50">{step}</span>
            </li>
          ))}
        </ol>
      </Panel>

      <CsvUploadPanel />
    </div>
  );
}

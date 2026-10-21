import type { Metadata } from 'next';

import { PageHero } from '@/components/site/page-hero';
import { SpotlightCard } from '@/components/site/spotlight-card';

export const metadata: Metadata = {
  title: 'Privacy',
  description: 'How FreightPilot handles workspace, operational, payment-evidence, and provider data.',
};

export default function PrivacyPage() {
  return (
    <>
      <PageHero
        eyebrow="Privacy"
        title="Know what the workspace holds"
        description="This page explains the data FreightPilot processes and the controls available to a workspace owner. It is product documentation, not a substitute for a signed customer data-processing agreement."
      />

      <section className="section-shell py-12 sm:py-16">
        <div className="grid gap-4 lg:grid-cols-2">
          <SpotlightCard>
            <h2 className="font-display text-2xl text-white">Data we process</h2>
            <ul className="mt-4 space-y-3 text-sm leading-7 text-white/65">
              <li>Account and workspace details: company name, business email, user name, role, and contact phone.</li>
              <li>Operational records you upload or create: warehouses, items, inventory, orders, shipments, routes, drivers, customers, and delivery stops.</li>
              <li>Execution evidence: delivery status, last known location, proof-of-delivery files, recipient confirmation, and cash declarations.</li>
              <li>Commercial evidence: subscription invoices, bank-transfer receipts, verification decisions, and audit events.</li>
              <li>Technical data: request IDs, timestamps, usage counters, health checks, and error diagnostics.</li>
            </ul>
          </SpotlightCard>
          <SpotlightCard>
            <h2 className="font-display text-2xl text-white">Why we process it</h2>
            <ul className="mt-4 space-y-3 text-sm leading-7 text-white/65">
              <li>To operate the workspace and execute the features you request.</li>
              <li>To authenticate users and enforce workspace roles and tenant boundaries.</li>
              <li>To produce route, forecast, exception, and cash-reconciliation evidence.</li>
              <li>To detect abuse, investigate errors, and maintain service security.</li>
              <li>To calculate subscription usage and process bank-transfer evidence.</li>
            </ul>
          </SpotlightCard>
        </div>
      </section>

      <section className="section-shell pb-12 sm:pb-16">
        <SpotlightCard>
          <h2 className="font-display text-2xl text-white">Storage, providers, and retention</h2>
          <div className="mt-4 grid gap-5 text-sm leading-7 text-white/65 lg:grid-cols-2">
            <div className="space-y-3">
              <p>
                FreightPilot uses hosted infrastructure for the web application, API, database, and
                operational logs. A workspace owner may configure a supported external AI provider
                key; provider requests are made only when that workspace uses the relevant feature.
              </p>
              <p>
                Operational records remain available for the life of the workspace unless a
                workspace owner requests deletion or the product documentation states a shorter
                retention period. Backup copies may persist for a bounded disaster-recovery window.
              </p>
            </div>
            <div className="space-y-3">
              <p>
                Proof-of-delivery files, bank-transfer evidence, and cash declarations are
                confidential workspace data. They are not sold or used to train a shared public
                model. A provider may process data under its own terms when a workspace explicitly
                configures that provider.
              </p>
              <p>
                To request access, correction, export, or deletion, contact the workspace owner or
                use the contact page. We may need to verify the request before acting.
              </p>
            </div>
          </div>
        </SpotlightCard>
      </section>

      <section className="section-shell pb-16">
        <SpotlightCard>
          <h2 className="font-display text-2xl text-white">Your choices and rights</h2>
          <p className="mt-4 max-w-[60rem] text-sm leading-8 text-white/65">
            Workspace owners control membership and provider configuration. Users should contact
            their workspace administrator for access or correction requests. We do not use
            third-party advertising trackers on the operator console. Privacy questions can be sent
            through the contact page; we will route them to the appropriate workspace or service
            owner.
          </p>
        </SpotlightCard>
      </section>
    </>
  );
}

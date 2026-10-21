import type { Metadata } from 'next';

import { PageHero } from '@/components/site/page-hero';
import { SpotlightCard } from '@/components/site/spotlight-card';

export const metadata: Metadata = {
  title: 'Security',
  description: 'FreightPilot security controls, limitations, and vulnerability reporting.',
};

export default function SecurityPage() {
  return (
    <>
      <PageHero
        eyebrow="Security"
        title="Security is part of the operating record"
        description="FreightPilot is designed around workspace membership, tenant-scoped data access, auditable actions, and explicit operational evidence. This page states the controls and the remaining limits plainly."
      />

      <section className="section-shell py-12 sm:py-16">
        <div className="grid gap-4 lg:grid-cols-2">
          <SpotlightCard>
            <h2 className="font-display text-2xl text-white">Controls in place</h2>
            <ul className="mt-4 space-y-3 text-sm leading-7 text-white/65">
              <li>Authenticated access with role checks and active workspace membership on business endpoints.</li>
              <li>Organization-scoped reads and writes; cross-tenant record access returns 404 rather than revealing existence.</li>
              <li>HTTP-only, same-site authentication cookies; the console SPA also uses a short-lived bearer token held in tab-scoped session storage, with cache clearing on account switches.</li>
              <li>Encrypted provider credentials at rest; keys are masked in the interface and can be revoked.</li>
              <li>Audit events for sensitive workspace, route, payment, and provider actions.</li>
              <li>Hash-pinned backend dependencies and dependency-audit gates in CI.</li>
            </ul>
          </SpotlightCard>
          <SpotlightCard>
            <h2 className="font-display text-2xl text-white">Current limits</h2>
            <ul className="mt-4 space-y-3 text-sm leading-7 text-white/65">
              <li>This is not a claim of SOC 2, ISO 27001, PCI-DSS, or another third-party certification.</li>
              <li>FreightPilot does not take custody of funds, provide escrow, or guarantee a carrier payment.</li>
              <li>Public docs and status pages are informational; a signed enterprise agreement controls support and incident commitments.</li>
              <li>External AI providers are optional and governed by the workspace owner's provider relationship.</li>
              <li>Independent security review and customer-specific threat modeling should precede high-risk deployment.</li>
            </ul>
          </SpotlightCard>
        </div>
      </section>

      <section className="section-shell pb-16">
        <SpotlightCard>
          <h2 className="font-display text-2xl text-white">Report a vulnerability</h2>
          <p className="mt-4 max-w-[60rem] text-sm leading-8 text-white/65">
            Do not include production secrets, customer data, or personal information in a public
            issue. Contact the team through the contact page with a concise description, affected
            surface, reproduction steps, and the minimum evidence needed to validate the report. We
            will acknowledge the report and coordinate disclosure according to the risk and the
            affected workspace.
          </p>
        </SpotlightCard>
      </section>
    </>
  );
}

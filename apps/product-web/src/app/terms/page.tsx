import type { Metadata } from 'next';

import { PageHero } from '@/components/site/page-hero';
import { SpotlightCard } from '@/components/site/spotlight-card';

export const metadata: Metadata = {
  title: 'Terms',
  description: 'FreightPilot workspace and service terms.',
};

export default function TermsPage() {
  return (
    <>
      <PageHero
        eyebrow="Terms"
        title="Clear terms for an operational system"
        description="These terms describe the baseline use of FreightPilot. A paid or enterprise engagement may add a signed order form, data-processing terms, or service-level terms."
      />

      <section className="section-shell py-12 sm:py-16">
        <div className="grid gap-4 lg:grid-cols-2">
          <SpotlightCard>
            <h2 className="font-display text-2xl text-white">Using the service</h2>
            <ul className="mt-4 space-y-3 text-sm leading-7 text-white/65">
              <li>You must have authority to create or administer the company workspace.</li>
              <li>You are responsible for the accuracy of the operational data you import and for the actions you approve.</li>
              <li>You must keep workspace credentials and provider keys secure and remove access when a teammate leaves.</li>
              <li>Do not use the service to violate law, infringe rights, distribute malware, or attempt unauthorized access to another workspace.</li>
              <li>Route, forecast, cash-risk, and exception recommendations are decision support. An authorized operator remains responsible for dispatch, payment, and customer decisions.</li>
            </ul>
          </SpotlightCard>
          <SpotlightCard>
            <h2 className="font-display text-2xl text-white">Commercial terms</h2>
            <ul className="mt-4 space-y-3 text-sm leading-7 text-white/65">
              <li>Published Free and paid tiers are described on the pricing page.</li>
              <li>Bank-transfer evidence is reviewed by the operator; a submitted receipt does not by itself prove settlement.</li>
              <li>The workspace may be locked for billing, security, or operational reasons while preserving read access where documented.</li>
              <li>Tier, usage, and overage terms may change with notice; a signed enterprise order takes precedence over this page.</li>
              <li>Features described as simulated, limited, or planned are not a promise of production availability.</li>
            </ul>
          </SpotlightCard>
        </div>
      </section>

      <section className="section-shell pb-16">
        <SpotlightCard>
          <h2 className="font-display text-2xl text-white">Availability, liability, and termination</h2>
          <p className="mt-4 max-w-[62rem] text-sm leading-8 text-white/65">
            We work to keep the service available and recoverable, but the public site does not
            promise an enterprise service-level objective. To the extent permitted by applicable
            law, FreightPilot is not liable for indirect or consequential loss, lost profit, or
            decisions made without operator review. A workspace owner may stop using the service at
            any time. We may suspend a workspace for abuse, non-payment, or a security risk. Before
            termination, export the operational data you need to retain; deletion and backup
            windows are described on the privacy page.
          </p>
          <p className="mt-4 text-sm leading-7 text-white/65">
            Questions about these terms can be sent through the contact page.
          </p>
        </SpotlightCard>
      </section>
    </>
  );
}

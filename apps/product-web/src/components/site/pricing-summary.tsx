import {
  freeLine,
  partialPaymentStory,
  pricingTiers,
} from '@/lib/site-content';

function formatEtb(value: number): string {
  return `${value.toLocaleString('en-US')} ETB`;
}

/**
 * Compact pricing summary (NB-39): 3 paid-tier rows + Free line +
 * partial-payment story. Server component — static, zero motion.
 */
export function PricingSummary() {
  return (
    <section className="section-shell pt-14 sm:pt-18" data-section="pricing-summary">
      <div className="glass-panel px-5 py-8 sm:px-8 sm:py-10">
        <p className="kicker">Pricing</p>
        <h2 className="mt-4 max-w-[20ch] font-display text-[clamp(1.75rem,3.6vw,2.9rem)] leading-[0.98] tracking-[-0.02em] text-white">
          Simple prices in ETB
        </h2>

        <div className="mt-8 overflow-x-auto">
          <table className="w-full min-w-[600px] border-collapse text-left">
            <thead>
              <tr className="border-b border-white/10 text-[11px] font-medium uppercase tracking-wide text-white/48">
                <th scope="col" className="pb-3 pr-4">Tier</th>
                <th scope="col" className="pb-3 pr-4">Flat price</th>
                <th scope="col" className="pb-3 pr-4">Billing cycle</th>
                <th scope="col" className="pb-3">What&rsquo;s included</th>
              </tr>
            </thead>
            <tbody>
              {pricingTiers.map((tier) => (
                <tr key={tier.name} className="border-b border-white/[0.06] last:border-0">
                  <td className="py-4 pr-4 font-display text-lg text-white">{tier.name}</td>
                  <td className="py-4 pr-4 text-sm text-white/78">{formatEtb(tier.price_etb)}</td>
                  <td className="py-4 pr-4 text-sm text-white/78">{tier.billing_cycle}</td>
                  <td className="py-4 text-sm leading-6 text-white/68">{tier.summary}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <p className="mt-8 font-display text-lg text-white">{freeLine}</p>
        <p className="mt-4 max-w-[44rem] text-sm leading-7 text-white/68">{partialPaymentStory}</p>
      </div>
    </section>
  );
}

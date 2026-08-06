import type { Metadata } from 'next';
import { BadgeCheck, CircleHelp } from 'lucide-react';

import { FaqAccordion } from '@/components/site/faq-accordion';
import { MagneticLink } from '@/components/site/magnetic-link';
import { PageHero } from '@/components/site/page-hero';
import { SectionHeading } from '@/components/site/section-heading';
import { SpotlightCard } from '@/components/site/spotlight-card';
import {
  faqItems,
  partialPaymentStory,
  paymentPaceStory,
  pricingTiers,
  startFreeCta,
  verificationLine,
} from '@/lib/site-content';

export const metadata: Metadata = {
  title: 'Pricing',
  description:
    'Start free forever — 2,500 delivery tasks per month. Paid tiers from 4,500 ETB per month. Pay by bank transfer to CBE or Dashen, no card required.',
};

function formatEtb(value: number): string {
  return `${value.toLocaleString('en-US')} ETB`;
}

function formatEtbRate(value: number): string {
  return `${value.toFixed(2)} ETB`;
}

/* FAQ structured data for SEO */
const faqJsonLd = {
  '@context': 'https://schema.org',
  '@type': 'FAQPage',
  mainEntity: faqItems.map((item) => ({
    '@type': 'Question',
    name: item.question,
    acceptedAnswer: {
      '@type': 'Answer',
      text: item.answer,
    },
  })),
};

export default function PricingPage() {
  return (
    <>
      {/* JSON-LD structured data */}
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(faqJsonLd) }}
      />

      <PageHero
        eyebrow="Pricing"
        title="Simple prices in ETB"
        description="Start on the Free tier forever. Upgrade from inside your workspace when you outgrow it, and pay by bank transfer to CBE or Dashen — no card required."
        actions={
          <MagneticLink href="/launch" variant="primary">
            {startFreeCta}
          </MagneticLink>
        }
      />

      <section className="section-shell pt-16 sm:pt-20">
        <SectionHeading
          eyebrow="Paid tiers"
          title="Three tiers with flat prices and clear overage rates"
          description="Every paid tier has a flat price and clear overage rates. The price shown is the price."
        />
        <div className="mt-10 grid gap-4 xl:grid-cols-3">
          {pricingTiers.map((tier) => {
            const bullets: string[] = [];
            if (tier.included_units.delivery_tasks !== null) {
              bullets.push(`${tier.included_units.delivery_tasks.toLocaleString('en-US')} delivery tasks included`);
            } else {
              bullets.push('Unlimited delivery tasks');
            }
            if (tier.included_units.route_optimizations !== null) {
              bullets.push(`${tier.included_units.route_optimizations.toLocaleString('en-US')} route optimizations included`);
            } else {
              bullets.push('Unlimited route optimizations');
            }
            if (tier.overage_rates.delivery_tasks !== null && tier.overage_rates.route_optimizations !== null) {
              bullets.push(
                `Extra delivery tasks: ${formatEtbRate(tier.overage_rates.delivery_tasks)} each`,
                `Extra route optimizations: ${formatEtbRate(tier.overage_rates.route_optimizations)} each`,
              );
            } else {
              bullets.push('No overage rates');
            }

            return (
              <SpotlightCard key={tier.name}>
                <p className="kicker">{tier.billing_cycle}</p>
                <h3 className="mt-4 font-display text-3xl text-white">{tier.name}</h3>
                <p className="mt-4 font-display text-[clamp(2rem,5vw,3.2rem)] text-white">{formatEtb(tier.price_etb)}</p>
                <p className="mt-3 text-sm leading-7 text-white/60">{tier.summary}</p>
                <ul className="mt-6 space-y-3 text-sm text-white/62">
                  {bullets.map((bullet) => (
                    <li key={bullet} className="flex items-start gap-3">
                      <BadgeCheck className="mt-0.5 h-4 w-4 shrink-0 text-cyan-200" />
                      <span>{bullet}</span>
                    </li>
                  ))}
                </ul>
                <div className="mt-8">
                  <MagneticLink href="/launch" variant="secondary">
                    {startFreeCta}
                  </MagneticLink>
                </div>
              </SpotlightCard>
            );
          })}
        </div>
      </section>

      <section className="section-shell pt-16 sm:pt-20">
        <SpotlightCard>
          <SectionHeading
            eyebrow="Payments"
            title="Pay by bank transfer to CBE or Dashen"
            description="No card is ever required. Partial payments are welcome at any point."
          />
          <p className="mt-8 max-w-[46rem] text-sm leading-8 text-white/72">{partialPaymentStory}</p>
          <p className="mt-4 text-sm leading-8 text-white/72">{paymentPaceStory}</p>
          <p className="mt-4 text-sm font-semibold text-white">{verificationLine}</p>
        </SpotlightCard>
      </section>

      <section className="section-shell py-16 sm:py-20">
        <div className="grid gap-4 lg:grid-cols-[0.9fr_1.1fr]">
          <div>
            <SectionHeading
              eyebrow="Questions"
              title="Frequently asked questions"
              description="Commercial details, the free tier, and paid-tier terms explained plainly."
            />
          </div>
          <div>
            <FaqAccordion items={faqItems} />
          </div>
        </div>
      </section>
    </>
  );
}

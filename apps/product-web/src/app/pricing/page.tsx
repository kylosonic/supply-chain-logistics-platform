import type { Metadata } from 'next';
import { BadgeCheck, CircleHelp, Sparkles } from 'lucide-react';

import { FaqAccordion } from '@/components/site/faq-accordion';
import { MagneticLink } from '@/components/site/magnetic-link';
import { MotionSection } from '@/components/site/motion-section';
import { PageHero } from '@/components/site/page-hero';
import { SectionHeading } from '@/components/site/section-heading';
import { SpotlightCard } from '@/components/site/spotlight-card';
import { faqItems, pricingTiers, testimonials } from '@/lib/site-content';

export const metadata: Metadata = {
  title: 'Pricing',
};

export default function PricingPage() {
  return (
    <>
      <PageHero
        eyebrow="Pricing"
        title="Clear pricing for rollout, operations, and scale"
        description="FreightPilot pricing is organized around operating footprint, user count, and launch support so teams can match the product to how they actually deploy it."
        actions={
          <>
            <MagneticLink href="/launch" variant="primary">
              Start a workspace
            </MagneticLink>
            <MagneticLink href="/technology" variant="secondary">
              Explore the AI stack
            </MagneticLink>
          </>
        }
      />

      <MotionSection className="section-shell pt-16 sm:pt-20" delay={0.06}>
        <SectionHeading
          eyebrow="Pricing tiers"
          title="Choose a plan that matches the way the team operates"
          description="Each plan is based on operating scope, rollout needs, and the level of control required by the team."
        />
        <div className="mt-10 grid gap-4 xl:grid-cols-3">
          {pricingTiers.map((tier, index) => (
            <SpotlightCard key={tier.name} className={index === 1 ? 'border-cyan-300/25 bg-white/[0.06]' : ''}>
              <div className="flex items-start justify-between gap-4">
                <div>
                  <p className="kicker">{tier.eyebrow}</p>
                  <h3 className="mt-4 font-display text-3xl text-white">{tier.name}</h3>
                </div>
                {index === 1 ? <span className="pill"><Sparkles className="h-4 w-4" /> Recommended plan</span> : null}
              </div>
              <p className="mt-4 font-display text-[clamp(2rem,5vw,3.4rem)] text-white">{tier.price}</p>
              <p className="mt-3 text-sm leading-7 text-white/58">{tier.summary}</p>
              <ul className="mt-6 space-y-3 text-sm text-white/62">
                {tier.bullets.map((bullet) => (
                  <li key={bullet} className="flex items-start gap-3">
                    <BadgeCheck className="mt-0.5 h-4 w-4 text-cyan-200" />
                    <span>{bullet}</span>
                  </li>
                ))}
              </ul>
              <div className="mt-8">
                <MagneticLink href="/launch" variant={index === 1 ? 'primary' : 'secondary'}>
                  {tier.cta}
                </MagneticLink>
              </div>
            </SpotlightCard>
          ))}
        </div>
      </MotionSection>

      <MotionSection className="section-shell pt-16 sm:pt-20" delay={0.08}>
        <div className="grid gap-4 lg:grid-cols-[1.05fr_0.95fr]">
          <SpotlightCard>
            <SectionHeading
              eyebrow="Value model"
              title="The business case is operational first"
              description="Route savings, service stability, rollout speed, and workspace governance all contribute to the value case."
            />
            <div className="mt-8 grid gap-3 sm:grid-cols-2">
              {[
                ['Route savings', 'Quantify distance, duration, and cost improvements.'],
                ['Failure reduction', 'Reduce missed windows and delayed-service recovery cost.'],
                ['Launch speed', 'Compress the time between procurement and first live dispatch.'],
                ['Governance', 'Keep provider, billing, and audit posture visible from day one.'],
              ].map(([title, detail]) => (
                <div key={title} className="rounded-[20px] border border-white/10 bg-black/25 p-4">
                  <p className="font-display text-xl text-white">{title}</p>
                  <p className="mt-3 text-sm leading-7 text-white/58">{detail}</p>
                </div>
              ))}
            </div>
          </SpotlightCard>

          <SpotlightCard>
            <CircleHelp className="h-6 w-6 text-cyan-200" />
            <h3 className="mt-5 font-display text-3xl text-white">Frequently asked questions</h3>
            <p className="mt-3 text-sm leading-7 text-white/58">Answer the commercial and architectural questions without falling back to generic category language.</p>
            <div className="mt-6">
              <FaqAccordion items={faqItems} />
            </div>
          </SpotlightCard>
        </div>
      </MotionSection>

      <MotionSection className="section-shell py-16 sm:py-20" delay={0.1}>
        <div className="grid gap-4 lg:grid-cols-3">
          {testimonials.map((item) => (
            <SpotlightCard key={item.company}>
              <p className="kicker">{item.company}</p>
              <p className="mt-5 text-lg leading-8 text-white">“{item.quote}”</p>
              <div className="mt-6 text-sm text-white/52">
                <p className="font-semibold text-white">{item.person}</p>
                <p>{item.role}</p>
              </div>
            </SpotlightCard>
          ))}
        </div>
      </MotionSection>
    </>
  );
}
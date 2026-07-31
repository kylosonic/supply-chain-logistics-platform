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
  description:
    'FreightPilot pricing is organized around operating footprint, user count, and launch support. Choose Starter, Scale, or Enterprise plans for your logistics operations.',
};

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
          {pricingTiers.map((tier, index) => {
            const isRecommended = index === 1;
            return (
              <SpotlightCard
                key={tier.name}
                className={
                  isRecommended
                    ? 'border-cyan-300/30 bg-white/[0.07] shadow-glow-lg ring-1 ring-cyan-400/15'
                    : ''
                }
              >
                <div className="flex items-start justify-between gap-4">
                  <div>
                    <p className="kicker">{tier.eyebrow}</p>
                    <h3 className="mt-4 font-display text-3xl text-white">{tier.name}</h3>
                  </div>
                  {isRecommended ? (
                    <span className="inline-flex items-center gap-2 rounded-full border border-cyan-300/25 bg-cyan-300/10 px-3 py-2 text-xs font-semibold uppercase tracking-[0.14em] text-cyan-100 shadow-[0_0_20px_rgba(34,211,238,0.12)]">
                      <Sparkles className="h-3.5 w-3.5 animate-pulse-glow" />
                      Most popular
                    </span>
                  ) : null}
                </div>
                <p className="mt-4 font-display text-[clamp(2rem,5vw,3.4rem)] text-white">{tier.price}</p>
                <p className="mt-3 text-sm leading-7 text-white/60">{tier.summary}</p>
                <ul className="mt-6 space-y-3 text-sm text-white/62">
                  {tier.bullets.map((bullet) => (
                    <li key={bullet} className="flex items-start gap-3">
                      <BadgeCheck className="mt-0.5 h-4 w-4 shrink-0 text-cyan-200" />
                      <span>{bullet}</span>
                    </li>
                  ))}
                </ul>
                <div className="mt-8">
                  <MagneticLink href="/launch" variant={isRecommended ? 'primary' : 'secondary'}>
                    {tier.cta}
                  </MagneticLink>
                </div>
              </SpotlightCard>
            );
          })}
        </div>
      </MotionSection>

      <MotionSection className="section-shell pt-16 sm:pt-20" delay={0.06}>
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
                  <p className="mt-3 text-sm leading-7 text-white/60">{detail}</p>
                </div>
              ))}
            </div>
          </SpotlightCard>

          <SpotlightCard>
            <CircleHelp className="h-6 w-6 text-violet-300" />
            <h3 className="mt-5 font-display text-3xl text-white">Frequently asked questions</h3>
            <p className="mt-3 text-sm leading-7 text-white/60">Answer the commercial and architectural questions without falling back to generic category language.</p>
            <div className="mt-6">
              <FaqAccordion items={faqItems} />
            </div>
          </SpotlightCard>
        </div>
      </MotionSection>

      <MotionSection className="section-shell py-16 sm:py-20" delay={0.06}>
        <SectionHeading
          eyebrow="What operators are saying"
          title="Trusted by logistics teams at every scale"
          description="Teams use FreightPilot to reduce context switching, accelerate launches, and maintain governance."
          align="center"
        />
        <div className="mt-10 grid gap-4 lg:grid-cols-3">
          {testimonials.map((item) => (
            <SpotlightCard key={item.company}>
              <div className="flex items-center gap-4">
                <div className={`inline-flex h-12 w-12 shrink-0 items-center justify-center rounded-full bg-gradient-to-br ${item.avatarColor} font-display text-sm font-bold text-white shadow-lg`}>
                  {item.person.split(' ').map((n) => n[0]).join('')}
                </div>
                <div className="text-sm">
                  <p className="font-semibold text-white">{item.person}</p>
                  <p className="text-white/52">{item.role}</p>
                </div>
              </div>
              <p className="mt-5 text-lg leading-8 text-white/80">&ldquo;{item.quote}&rdquo;</p>
              <p className="mt-3 text-sm text-white/50">{item.company}</p>
            </SpotlightCard>
          ))}
        </div>
      </MotionSection>
    </>
  );
}
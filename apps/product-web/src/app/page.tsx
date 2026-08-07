import { HeroEntrance } from '@/components/site/hero-entrance';
import { HowItWorks } from '@/components/site/how-it-works';
import { MagneticLink } from '@/components/site/magnetic-link';
import { PricingSummary } from '@/components/site/pricing-summary';
import {
  heroHeadline,
  heroParagraph,
  startFreeCta,
  trustStripLine,
} from '@/lib/site-content';

export default function HomePage() {
  return (
    <>
      <section className="section-shell pt-6 sm:pt-10 lg:pt-12" data-section="hero">
        <div className="glass-panel px-6 py-10 sm:px-10 sm:py-14">
          <div className="max-w-[46rem] space-y-7">
            <p className="kicker">FreightPilot</p>
            <HeroEntrance />
            <p className="lede text-base sm:text-lg">{heroParagraph}</p>
            <div className="pt-2">
              <MagneticLink href="/launch" variant="primary" className="min-h-14 px-8 text-base">
                {startFreeCta}
              </MagneticLink>
            </div>
          </div>
        </div>
      </section>

      <HowItWorks />

      <PricingSummary />

      <section className="section-shell pt-14 sm:pt-18" data-section="trust-strip">
        <p className="mx-auto max-w-[34rem] text-balance text-center text-sm leading-6 text-white/72 sm:text-base">
          {trustStripLine}
        </p>
      </section>

      <section className="section-shell pb-8 pt-14 sm:pb-12 sm:pt-18" data-section="final-cta">
        <div className="flex justify-center">
          <MagneticLink href="/launch" variant="primary" className="min-h-16 px-10 text-lg">
            {startFreeCta}
          </MagneticLink>
        </div>
      </section>
    </>
  );
}

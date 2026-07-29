import { ArrowUpRight, BrainCircuit, ShieldCheck, Sparkles } from 'lucide-react';

import { AnimatedCounter } from '@/components/site/animated-counter';
import { HeroScene } from '@/components/site/hero-scene';
import { MagneticLink } from '@/components/site/magnetic-link';
import { MotionSection } from '@/components/site/motion-section';
import { SectionHeading } from '@/components/site/section-heading';
import { SpotlightCard } from '@/components/site/spotlight-card';
import {
  benefitStrip,
  externalLinks,
  flagshipFeatures,
  homeStats,
  operatingLoop,
  platformNarrative,
  premiumBadges,
  secondaryFeatures,
  testimonials,
  trustSignals,
} from '@/lib/site-content';

export default function HomePage() {
  return (
    <>
      <section className="section-shell pt-4 sm:pt-8 lg:pt-10">
        <div className="grid gap-8 lg:grid-cols-[1.1fr_0.9fr] lg:items-start xl:gap-10">
          <div className="space-y-6 sm:space-y-7">
            <div className="space-y-5">
              <span className="pill">
                <Sparkles className="h-4 w-4" />
                FreightPilot operations platform
              </span>
              <h1 className="balanced-headline max-w-[13ch] font-display text-[clamp(2.3rem,4.35vw,4.15rem)] leading-[0.96] tracking-[-0.03em] text-white">
                Plan routes, manage exceptions, and launch operations from one control layer.
              </h1>
              <p className="lede text-base sm:text-lg">
                FreightPilot gives logistics teams a single workspace for route planning, live issue management,
                operator launch readiness, and AI-assisted decision support.
              </p>
            </div>

            <div className="flex flex-col items-stretch gap-3 sm:flex-row sm:flex-wrap sm:items-center [&>*]:w-full sm:[&>*]:w-auto">
              <MagneticLink href="/launch" variant="primary">
                Start workspace setup
              </MagneticLink>
              <MagneticLink href={externalLinks.console} variant="secondary" external>
                View control tower
              </MagneticLink>
            </div>

            <div className="grid gap-2 sm:flex sm:flex-wrap">
              {premiumBadges.map((badge) => (
                <span key={badge} className="rounded-full border border-white/10 bg-white/[0.04] px-3 py-2 text-xs text-white/56">
                  {badge}
                </span>
              ))}
            </div>
          </div>

          <div>
            <HeroScene />
          </div>
        </div>
      </section>

      <MotionSection className="section-shell pt-8 sm:pt-10" delay={0.07}>
        <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
          {homeStats.map((stat, index) => (
            <SpotlightCard key={stat.label} className="min-h-[188px]">
              <p className="kicker">{stat.label}</p>
              <p className="mt-4 font-display text-5xl text-white">
                <AnimatedCounter value={stat.value} suffix={stat.suffix} />
              </p>
              <p className="mt-3 text-sm leading-7 text-white/58">{stat.detail}</p>
              <div className="mt-4 h-px w-full bg-gradient-to-r from-cyan-300/0 via-cyan-300/50 to-cyan-300/0" />
              <span className="mt-4 inline-flex text-xs text-white/42">0{index + 1}</span>
            </SpotlightCard>
          ))}
        </div>
      </MotionSection>

      <MotionSection className="section-shell pt-16 sm:pt-20" delay={0.05}>
        <SectionHeading
          eyebrow="What the platform covers"
          title="Operational control without constant context switching"
          description="FreightPilot is built for teams that need planning, execution, launch readiness, and provider controls in the same product."
        />
        <div className="mt-10 grid gap-4 lg:grid-cols-2 xl:grid-cols-4">
          {flagshipFeatures.map((feature) => (
            <SpotlightCard key={feature.title}>
              <feature.icon className="h-6 w-6 text-cyan-200" />
              <h3 className="mt-5 font-display text-2xl text-white">{feature.title}</h3>
              <p className="mt-3 text-sm leading-7 text-white/62">{feature.description}</p>
              <p className="mt-5 text-sm leading-7 text-white/46">{feature.detail}</p>
            </SpotlightCard>
          ))}
        </div>
      </MotionSection>

      <MotionSection className="section-shell pt-16 sm:pt-20" delay={0.08}>
        <SectionHeading
          eyebrow="How teams use it"
          title="A simple loop for daily operations"
          description="The core workflow is straightforward: surface issues, choose an action with the right context, and record what changed."
        />
        <div className="mt-10 grid gap-4 lg:grid-cols-3">
          {operatingLoop.map((item) => (
            <div key={item.title} className="glass-panel rounded-[30px] px-6 py-6">
              <span className="kicker">{item.label}</span>
              <h3 className="mt-4 font-display text-3xl text-white">{item.title}</h3>
              <p className="mt-4 text-sm leading-7 text-white/58">{item.detail}</p>
            </div>
          ))}
        </div>
      </MotionSection>

      <MotionSection className="section-shell pt-16 sm:pt-20" delay={0.1}>
        <div className="glass-panel rounded-[34px] px-6 py-8 sm:px-8">
          <SectionHeading
            eyebrow="Grounded product information"
            title="Messaging that maps to actual workflows"
            description="The product story is tied directly to routing, alert handling, workspace setup, usage controls, and audit history."
          />
          <div className="mt-10 grid gap-4 lg:grid-cols-3">
            {platformNarrative.map((item) => (
              <SpotlightCard key={item}>
                <ShieldCheck className="h-6 w-6 text-violet-200" />
                <p className="mt-5 text-base leading-8 text-white/68">{item}</p>
              </SpotlightCard>
            ))}
          </div>
          <div className="mt-8 flex flex-wrap gap-2">
            {trustSignals.map((signal) => (
              <span key={signal} className="rounded-full border border-white/10 bg-white/[0.05] px-3 py-2 text-xs text-white/54">
                {signal}
              </span>
            ))}
          </div>
        </div>
      </MotionSection>

      <MotionSection className="section-shell pt-16 sm:pt-20" delay={0.12}>
        <SectionHeading
          eyebrow="Browse by workflow"
          title="Each page answers a different operating question"
          description="Move through platform structure, provider controls, pricing, and workspace setup without losing the same visual system."
        />
        <div className="mt-10 grid gap-4 lg:grid-cols-4">
          {secondaryFeatures.map((feature) => (
            <SpotlightCard key={feature.title}>
              <feature.icon className="h-6 w-6 text-cyan-200" />
              <h3 className="mt-5 font-display text-2xl text-white">{feature.title}</h3>
              <p className="mt-3 text-sm leading-7 text-white/58">{feature.description}</p>
              <p className="mt-5 text-sm leading-7 text-white/42">{feature.detail}</p>
            </SpotlightCard>
          ))}
        </div>
      </MotionSection>

      <MotionSection className="section-shell pt-16 sm:pt-20" delay={0.14}>
        <div className="grid gap-4 lg:grid-cols-3">
          {testimonials.map((item) => (
            <SpotlightCard key={item.company}>
              <BrainCircuit className="h-6 w-6 text-cyan-200" />
              <p className="mt-5 text-lg leading-8 text-white">“{item.quote}”</p>
              <div className="mt-6 text-sm text-white/52">
                <p className="font-semibold text-white">{item.person}</p>
                <p>{item.role}</p>
                <p className="mt-1 text-white/38">{item.company}</p>
              </div>
            </SpotlightCard>
          ))}
        </div>
      </MotionSection>

      <MotionSection className="section-shell pb-8 pt-14 sm:pb-10 sm:pt-18" delay={0.16}>
        <div className="glass-panel rounded-[38px] px-6 py-8 sm:px-8 sm:py-10">
          <div className="grid gap-8 lg:grid-cols-[1.08fr_0.92fr] lg:items-end">
            <div>
              <p className="kicker">Next step</p>
              <h2 className="balanced-headline mt-4 max-w-[12ch] font-display text-[clamp(2rem,5vw,4.5rem)] leading-[0.92] tracking-[-0.03em] text-white">
                Start with a clear rollout plan and one operational workspace.
              </h2>
              <p className="mt-4 max-w-2xl text-sm leading-8 text-white/62">
                Review the product by workflow or move directly into workspace setup if the team is ready to begin a pilot.
              </p>
            </div>
            <div className="flex flex-col gap-3 sm:flex-row lg:justify-end lg:self-end">
              <MagneticLink href="/platform" variant="secondary">
                Explore platform
              </MagneticLink>
              <MagneticLink href="/launch" variant="primary">
                Start launch flow
              </MagneticLink>
            </div>
          </div>
          <div className="mt-8 flex flex-wrap gap-2">
            {benefitStrip.map((item) => (
              <span key={item} className="rounded-full border border-white/10 bg-black/20 px-3 py-2 text-xs text-white/54">
                {item}
              </span>
            ))}
          </div>
        </div>
      </MotionSection>
    </>
  );
}
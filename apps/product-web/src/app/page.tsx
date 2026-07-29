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
      <section className="section-shell pt-8 sm:pt-12 lg:pt-16">
        <div className="grid gap-8 lg:grid-cols-[1.05fr_0.95fr] lg:items-start">
          <MotionSection className="space-y-6" delay={0.05}>
            <div className="space-y-5">
              <span className="pill">
                <Sparkles className="h-4 w-4" />
                FreightPilot 2026 launch
              </span>
              <h1 className="max-w-5xl font-display text-[clamp(3.1rem,8vw,7rem)] leading-[0.88] text-white">
                The logistics command layer for teams who want the future to feel real.
              </h1>
              <p className="max-w-2xl text-base leading-8 text-white/66 sm:text-lg">
                FreightPilot is rebuilt from the ground up as a cinematic, AI-native product experience that feels more
                like a frontier operating system than a SaaS dashboard.
              </p>
            </div>

            <div className="flex flex-wrap gap-3">
              <MagneticLink href="/launch" variant="primary">
                Create company workspace
              </MagneticLink>
              <MagneticLink href={externalLinks.console} variant="secondary" external>
                Open control tower
              </MagneticLink>
            </div>

            <div className="flex flex-wrap gap-2">
              {premiumBadges.map((badge) => (
                <span key={badge} className="rounded-full border border-white/10 bg-white/[0.04] px-3 py-2 text-xs text-white/56">
                  {badge}
                </span>
              ))}
            </div>

            <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
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

          <MotionSection delay={0.14}>
            <HeroScene />
          </MotionSection>
        </div>
      </section>

      <MotionSection className="section-shell pt-20" delay={0.05}>
        <SectionHeading
          eyebrow="Why this feels different"
          title="Premium design as an operating advantage"
          description="Every surface is intentionally shaped to feel calm, high-context, and expensive. No templates. No default SaaS chrome. Just product theater with operational credibility."
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

      <MotionSection className="section-shell pt-20" delay={0.08}>
        <SectionHeading
          eyebrow="Operating loop"
          title="Every page reveals a different layer of the system"
          description="The new site is structured like a product launch journey: first the promise, then the platform, then the AI stack, then the commercial model, then the launch ritual."
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

      <MotionSection className="section-shell pt-20" delay={0.1}>
        <div className="glass-panel rounded-[34px] px-6 py-8 sm:px-8">
          <SectionHeading
            eyebrow="Platform identity"
            title="A product story that still maps to real functionality"
            description="The content is grounded in the actual routing, alerting, planning, launch, and governance workflows already living in FreightPilot."
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

      <MotionSection className="section-shell pt-20" delay={0.12}>
        <SectionHeading
          eyebrow="Page preview"
          title="The experience keeps unfolding as you move through the stack"
          description="Each route below is its own scene: product architecture, AI orchestration, pricing clarity, and workspace launch."
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

      <MotionSection className="section-shell pt-20" delay={0.14}>
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

      <MotionSection className="section-shell py-20" delay={0.16}>
        <div className="glass-panel rounded-[38px] px-6 py-8 sm:px-8 sm:py-10">
          <div className="grid gap-8 lg:grid-cols-[1.05fr_0.95fr] lg:items-center">
            <div>
              <p className="kicker">Ready to launch</p>
              <h2 className="mt-4 font-display text-[clamp(2rem,5vw,4.5rem)] leading-[0.92] text-white">
                Move from curiosity into a premium launch sequence.
              </h2>
              <p className="mt-4 max-w-2xl text-sm leading-8 text-white/62">
                Explore the platform page by page or skip ahead and open the workspace launch flow. Everything is
                designed to feel fast, intelligent, and unforgettable.
              </p>
            </div>
            <div className="flex flex-col gap-3 sm:flex-row lg:justify-end">
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
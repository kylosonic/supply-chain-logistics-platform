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

/* Diversified icon accent colors per section */
const featureIconColors = ['text-cyan-200', 'text-violet-300', 'text-amber-200', 'text-emerald-200'];
const secondaryIconColors = ['text-violet-300', 'text-amber-200', 'text-emerald-200', 'text-cyan-200'];

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
              <h1 className="balanced-headline max-w-[16ch] font-display text-[clamp(2.3rem,4.35vw,4.15rem)] leading-[0.96] tracking-[-0.03em] text-white">
                Plan routes, manage exceptions, and launch operations from one control layer.
              </h1>
              <p className="lede text-base sm:text-lg">
                FreightPilot gives logistics teams a single workspace for route planning, live issue management,
                operator launch readiness, and AI-assisted decision support.
              </p>
            </div>

            <div className="flex flex-col items-stretch gap-3 sm:flex-row sm:flex-wrap sm:items-center [&>*]:w-full sm:[&>*]:w-auto">
              <MagneticLink href="/launch" variant="primary">
                Launch your workspace
              </MagneticLink>
              <MagneticLink href="/platform" variant="secondary">
                Explore the platform
              </MagneticLink>
            </div>

            <div className="grid gap-2 sm:flex sm:flex-wrap">
              {premiumBadges.map((badge) => (
                <span key={badge} className="rounded-full border border-white/10 bg-white/[0.04] px-3 py-2 text-xs text-white/60">
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

      {/* Glowing divider between hero and stats */}
      <div className="section-shell pt-10 sm:pt-12">
        <div className="divider-glow" />
      </div>

      <MotionSection className="section-shell pt-8 sm:pt-10" delay={0.05}>
        <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
          {homeStats.map((stat, index) => (
            <SpotlightCard key={stat.label} className="min-h-[188px]">
              <p className="kicker">{stat.label}</p>
              <p className="mt-4 font-display text-5xl text-white">
                <AnimatedCounter value={stat.value} suffix={stat.suffix} />
              </p>
              <p className="mt-3 text-sm leading-7 text-white/60">{stat.detail}</p>
              <div className="mt-4 h-px w-full bg-gradient-to-r from-cyan-300/0 via-cyan-300/50 to-cyan-300/0" />
              <span className="mt-4 inline-flex text-xs text-white/50">0{index + 1}</span>
            </SpotlightCard>
          ))}
        </div>
      </MotionSection>

      <MotionSection className="section-shell pt-16 sm:pt-20" delay={0.04}>
        <SectionHeading
          eyebrow="What the platform covers"
          title="Stop context switching. Start making decisions."
          description="FreightPilot brings planning, execution, launch readiness, and provider controls into one workspace so your team can act faster."
        />
        <div className="mt-10 grid gap-4 lg:grid-cols-2 xl:grid-cols-4">
          {flagshipFeatures.map((feature, index) => (
            <SpotlightCard key={feature.title}>
              <feature.icon className={`h-6 w-6 ${featureIconColors[index % featureIconColors.length]}`} />
              <h3 className="mt-5 font-display text-2xl text-white">{feature.title}</h3>
              <p className="mt-3 text-sm leading-7 text-white/62">{feature.description}</p>
              <p className="mt-5 text-sm leading-7 text-white/50">{feature.detail}</p>
            </SpotlightCard>
          ))}
        </div>
      </MotionSection>

      <MotionSection className="section-shell pt-16 sm:pt-20" delay={0.05}>
        <SectionHeading
          eyebrow="How teams use it"
          title="A simple loop for daily operations"
          description="Surface issues, choose an action with the right context, and record what changed — every day."
        />
        <div className="mt-10 grid gap-4 lg:grid-cols-3">
          {operatingLoop.map((item) => (
            <div key={item.title} className="glass-panel rounded-[30px] px-6 py-6">
              <span className="kicker">{item.label}</span>
              <h3 className="mt-4 font-display text-3xl text-white">{item.title}</h3>
              <p className="mt-4 text-sm leading-7 text-white/60">{item.detail}</p>
            </div>
          ))}
        </div>
      </MotionSection>

      <MotionSection className="section-shell pt-16 sm:pt-20" delay={0.06}>
        <div className="glass-panel rounded-[34px] px-6 py-8 sm:px-8">
          <SectionHeading
            eyebrow="Built on real workflows"
            title="Every feature maps to an actual operator task"
            description="The product is organized around routing, alert handling, workspace setup, usage controls, and audit history."
          />
          <div className="mt-10 grid gap-4 lg:grid-cols-3">
            {platformNarrative.map((item, index) => (
              <SpotlightCard key={`narrative-${index}`}>
                <ShieldCheck className={`h-6 w-6 ${index === 0 ? 'text-violet-300' : index === 1 ? 'text-emerald-200' : 'text-amber-200'}`} />
                <p className="mt-5 text-base leading-8 text-white/68">{item}</p>
              </SpotlightCard>
            ))}
          </div>
          <div className="mt-8 flex flex-wrap gap-2">
            {trustSignals.map((signal) => (
              <span key={signal} className="rounded-full border border-white/10 bg-white/[0.05] px-3 py-2 text-xs text-white/60">
                {signal}
              </span>
            ))}
          </div>
        </div>
      </MotionSection>

      <MotionSection className="section-shell pt-16 sm:pt-20" delay={0.06}>
        <SectionHeading
          eyebrow="Browse by workflow"
          title="Each page answers a different operating question"
          description="Move through platform structure, provider controls, pricing, and workspace setup without losing the same visual system."
        />
        <div className="mt-10 grid gap-4 lg:grid-cols-4">
          {secondaryFeatures.map((feature, index) => (
            <SpotlightCard key={feature.title}>
              <feature.icon className={`h-6 w-6 ${secondaryIconColors[index % secondaryIconColors.length]}`} />
              <h3 className="mt-5 font-display text-2xl text-white">{feature.title}</h3>
              <p className="mt-3 text-sm leading-7 text-white/60">{feature.description}</p>
              <p className="mt-5 text-sm leading-7 text-white/50">{feature.detail}</p>
            </SpotlightCard>
          ))}
        </div>
      </MotionSection>

      <MotionSection className="section-shell pt-16 sm:pt-20" delay={0.06}>
        <SectionHeading
          eyebrow="What operators are saying"
          title="Trusted by logistics teams at every scale"
          description="Teams use FreightPilot to reduce context switching, accelerate launches, and maintain governance across operations."
          align="center"
        />
        <div className="mt-10 grid gap-4 lg:grid-cols-3">
          {testimonials.map((item) => (
            <SpotlightCard key={item.company}>
              <div className="flex items-center gap-4">
                {/* Avatar circle with gradient initials */}
                <div className={`inline-flex h-12 w-12 shrink-0 items-center justify-center rounded-full bg-gradient-to-br ${item.avatarColor} font-display text-sm font-bold text-white shadow-lg`}>
                  {item.person.split(' ').map((n) => n[0]).join('')}
                </div>
                <div className="text-sm">
                  <p className="font-semibold text-white">{item.person}</p>
                  <p className="text-white/52">{item.role}</p>
                  <p className="text-white/40">{item.company}</p>
                </div>
              </div>
              <p className="mt-5 text-lg leading-8 text-white/80">&ldquo;{item.quote}&rdquo;</p>
            </SpotlightCard>
          ))}
        </div>
      </MotionSection>

      <MotionSection className="section-shell pb-8 pt-14 sm:pb-10 sm:pt-18" delay={0.06}>
        <div className="glass-panel rounded-[38px] px-6 py-8 sm:px-8 sm:py-10">
          <div className="grid gap-8 lg:grid-cols-[1.08fr_0.92fr] lg:items-end">
            <div>
              <p className="kicker">Next step</p>
              <h2 className="balanced-headline mt-4 max-w-[14ch] font-display text-[clamp(2rem,5vw,4.5rem)] leading-[0.92] tracking-[-0.03em] text-white">
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
              <span key={item} className="rounded-full border border-white/10 bg-black/20 px-3 py-2 text-xs text-white/60">
                {item}
              </span>
            ))}
          </div>
        </div>
      </MotionSection>
    </>
  );
}
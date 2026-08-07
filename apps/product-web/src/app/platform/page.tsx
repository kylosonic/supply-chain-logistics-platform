import type { Metadata } from 'next';
import { BadgeCheck, Gauge, Layers3, Route, Sparkles, Workflow } from 'lucide-react';

import { MagneticLink } from '@/components/site/magnetic-link';
import { MotionSection } from '@/components/site/motion-section';
import { PageHero } from '@/components/site/page-hero';
import { SectionHeading } from '@/components/site/section-heading';
import { SpotlightCard } from '@/components/site/spotlight-card';
import { operatingLoop, platformStacks, startFreeCta } from '@/lib/site-content';

export const metadata: Metadata = {
  title: 'Platform',
  description:
    'Explore how FreightPilot organizes route decisions, live exceptions, shipment flow, workspace controls, and rollout tasks into one operating system for logistics teams.',
};

const stackIconColors = ['text-cyan-200', 'text-violet-300', 'text-amber-200', 'text-emerald-200'];

export default function PlatformPage() {
  return (
    <>
      <PageHero
        eyebrow="Platform"
        title="A platform organized around real logistics work"
        description="FreightPilot brings route decisions, live exceptions, shipment flow, workspace controls, and rollout tasks into one operating system."
        actions={
          <MagneticLink href="/launch" variant="primary">
            {startFreeCta}
          </MagneticLink>
        }
        aside={
          <div className="grid gap-4">
            <SpotlightCard>
              <Layers3 className="h-6 w-6 text-cyan-200" />
              <p className="mt-5 font-display text-2xl text-white">Four product families. One operating rhythm.</p>
              <p className="mt-3 text-sm leading-7 text-white/60">Control Tower, Decision Studio, Launch Workstation, and Revenue Guard are presented as one ecosystem instead of fragmented modules.</p>
            </SpotlightCard>
          </div>
        }
      />

      <MotionSection className="section-shell pt-16 sm:pt-20" delay={0.06}>
        <SectionHeading
          eyebrow="Product stack"
          title="Each part of the product supports the same operating workflow"
          description="The platform is modular, but teams should still experience it as one connected system for planning, response, and rollout."
        />
        <div className="mt-10 grid gap-4 xl:grid-cols-4">
          {platformStacks.map((feature, index) => (
            <SpotlightCard key={feature.title}>
              <feature.icon className={`h-6 w-6 ${stackIconColors[index % stackIconColors.length]}`} />
              <h3 className="mt-5 font-display text-2xl text-white">{feature.title}</h3>
              <p className="mt-3 text-sm leading-7 text-white/60">{feature.description}</p>
              <p className="mt-5 text-sm leading-7 text-white/50">{feature.detail}</p>
            </SpotlightCard>
          ))}
        </div>
      </MotionSection>

      <MotionSection className="section-shell pt-16 sm:pt-20" delay={0.06}>
        <div className="grid gap-4 lg:grid-cols-[1.05fr_0.95fr]">
          <div className="glass-panel px-6 py-7">
            <SectionHeading
              eyebrow="How it works"
              title="Route decisions stay readable while pressure is high"
              description="Every stage of the workflow keeps the next action visible without forcing the team to leave the current operating context."
            />
            <div className="mt-10 space-y-4">
              {operatingLoop.map((item) => (
                <div key={item.title} className="rounded-[24px] border border-white/10 bg-black/25 p-5">
                  <span className="kicker">{item.label}</span>
                  <h3 className="mt-3 font-display text-2xl text-white">{item.title}</h3>
                  <p className="mt-3 text-sm leading-7 text-white/60">{item.detail}</p>
                </div>
              ))}
            </div>
          </div>

          <div className="grid gap-4">
            <SpotlightCard>
              <Route className="h-6 w-6 text-cyan-200" />
              <h3 className="mt-5 font-display text-2xl text-white">Route Studio</h3>
              <p className="mt-3 text-sm leading-7 text-white/60">Optimize, compare, and persist route scenarios with unassigned demand history visible after the run.</p>
              <div className="mt-6 grid gap-3 sm:grid-cols-2">
                {['Scenario history', 'Map review', 'Saved schedules', 'Operator handoff'].map((item) => (
                  <div key={item} className="rounded-[18px] border border-white/10 bg-black/30 px-4 py-3 text-sm text-white/62">
                    {item}
                  </div>
                ))}
              </div>
            </SpotlightCard>
            <SpotlightCard>
              <Gauge className="h-6 w-6 text-violet-300" />
              <h3 className="mt-5 font-display text-2xl text-white">Workspace commercial posture</h3>
              <p className="mt-3 text-sm leading-7 text-white/60">Usage metering, provider preference, and subscription posture belong in the same premium story as dispatch and routing.</p>
            </SpotlightCard>
          </div>
        </div>
      </MotionSection>

      <MotionSection className="section-shell py-16 sm:py-20" delay={0.06}>
        <SectionHeading
          eyebrow="Platform outcome"
          title="The product experience should stay coherent from website to workstation"
          description="FreightPilot is designed so the marketing site, operator console, and launch workstation all explain the same operating model."
          align="center"
        />
        <div className="mt-10 grid gap-4 md:grid-cols-3">
          {[
            { icon: Workflow, title: 'Operational coherence', detail: 'Routes, alerts, and launch state tell one story.', color: 'text-cyan-200' },
            { icon: Sparkles, title: 'Premium interaction design', detail: 'Glass layers, animated borders, and deep lighting make the product memorable.', color: 'text-violet-300' },
            { icon: BadgeCheck, title: 'Credible trust posture', detail: 'Audit trails and workspace governance keep the cinematic experience honest.', color: 'text-emerald-200' },
          ].map((item) => (
            <SpotlightCard key={item.title}>
              <item.icon className={`h-6 w-6 ${item.color}`} />
              <h3 className="mt-5 font-display text-2xl text-white">{item.title}</h3>
              <p className="mt-3 text-sm leading-7 text-white/60">{item.detail}</p>
            </SpotlightCard>
          ))}
        </div>
      </MotionSection>
    </>
  );
}
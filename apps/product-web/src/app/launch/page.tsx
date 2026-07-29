import type { Metadata } from 'next';
import { ArrowUpRight, BadgeCheck, Download, ShieldCheck } from 'lucide-react';

import { MagneticLink } from '@/components/site/magnetic-link';
import { MotionSection } from '@/components/site/motion-section';
import { PageHero } from '@/components/site/page-hero';
import { SectionHeading } from '@/components/site/section-heading';
import { SignupForm } from '@/components/site/signup-form';
import { SpotlightCard } from '@/components/site/spotlight-card';
import { deepLinks, launchSteps, trustSignals } from '@/lib/site-content';

export const metadata: Metadata = {
  title: 'Launch',
};

export default function LaunchPage() {
  return (
    <>
      <PageHero
        eyebrow="Launch"
        title="Set up the workspace and launch operations in stages"
        description="Create the workspace, prepare the launch workstation, and move the team into live operations with clear ownership and readiness checks."
        actions={
          <>
            <MagneticLink href={deepLinks.desktop} variant="secondary" external>
              <Download className="h-4 w-4" />
              Get desktop
            </MagneticLink>
            <MagneticLink href={deepLinks.docs} variant="ghost" external>
              Review docs
            </MagneticLink>
          </>
        }
      />

      <MotionSection className="section-shell pt-16 sm:pt-20" delay={0.06}>
        <div className="grid gap-4 lg:grid-cols-[1.02fr_0.98fr]">
          <SignupForm />
          <div className="grid gap-4">
            <SpotlightCard>
              <SectionHeading
                eyebrow="Launch sequence"
                title="Build the workspace in controlled stages"
                description="The launch flow is designed to keep setup, ownership, and readiness checks explicit from the first step." 
              />
              <div className="mt-8 space-y-4">
                {launchSteps.map((step) => (
                  <div key={step.title} className="rounded-[22px] border border-white/10 bg-black/25 p-4">
                    <span className="kicker">{step.label}</span>
                    <h3 className="mt-3 font-display text-2xl text-white">{step.title}</h3>
                    <p className="mt-3 text-sm leading-7 text-white/58">{step.detail}</p>
                  </div>
                ))}
              </div>
            </SpotlightCard>

            <SpotlightCard>
              <ShieldCheck className="h-6 w-6 text-cyan-200" />
              <h3 className="mt-5 font-display text-2xl text-white">Trust signals visible from the first click</h3>
              <div className="mt-5 flex flex-wrap gap-2">
                {trustSignals.map((signal) => (
                  <span key={signal} className="rounded-full border border-white/10 bg-white/[0.05] px-3 py-2 text-xs text-white/58">
                    {signal}
                  </span>
                ))}
              </div>
            </SpotlightCard>
          </div>
        </div>
      </MotionSection>

      <MotionSection className="section-shell py-16 sm:py-20" delay={0.08}>
        <SectionHeading
          eyebrow="After signup"
          title="Move from setup into the workstation and control tower"
          description="Use the desktop layer for launch readiness, then move into the control tower when the team is ready for live work."
        />
        <div className="mt-10 grid gap-4 lg:grid-cols-3">
          {[
            {
              icon: Download,
              title: 'Desktop launch workstation',
              detail: 'Validate console connectivity, role sign-off, and rollout readiness machine by machine.',
              href: deepLinks.desktop,
            },
            {
              icon: ArrowUpRight,
              title: 'Open the control tower',
              detail: 'Move directly into routes, alerts, planning, shipments, and workspace governance.',
              href: deepLinks.console,
            },
            {
              icon: BadgeCheck,
              title: 'Read the implementation docs',
              detail: 'Document the rollout process, product model, and AI governance approach for the team.',
              href: deepLinks.docs,
            },
          ].map((item) => (
            <SpotlightCard key={item.title}>
              <item.icon className="h-6 w-6 text-cyan-200" />
              <h3 className="mt-5 font-display text-2xl text-white">{item.title}</h3>
              <p className="mt-3 text-sm leading-7 text-white/58">{item.detail}</p>
              <div className="mt-6">
                <MagneticLink href={item.href} variant="secondary" external>
                  Open
                </MagneticLink>
              </div>
            </SpotlightCard>
          ))}
        </div>
      </MotionSection>
    </>
  );
}
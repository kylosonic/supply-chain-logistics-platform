import type { Metadata } from 'next';
import { ArrowRight, BrainCircuit, Cable, Cpu, Fingerprint, Radar, ShieldCheck } from 'lucide-react';

import { MagneticLink } from '@/components/site/magnetic-link';
import { MotionSection } from '@/components/site/motion-section';
import { PageHero } from '@/components/site/page-hero';
import { SectionHeading } from '@/components/site/section-heading';
import { SpotlightCard } from '@/components/site/spotlight-card';
import { codeSnippet, externalLinks, technologyLayers, trustRibbon } from '@/lib/site-content';

export const metadata: Metadata = {
  title: 'Technology',
};

export default function TechnologyPage() {
  return (
    <>
      <PageHero
        eyebrow="Technology"
        title="AI orchestration that feels visible, governed, and fast"
        description="The technology story is not hidden in an appendix. FreightPilot treats signal ingestion, model routing, workspace governance, and auditability as premium product features."
        actions={
          <>
            <MagneticLink href="/pricing" variant="primary">
              Explore pricing
            </MagneticLink>
            <MagneticLink href={externalLinks.docs} variant="secondary" external>
              Review docs
            </MagneticLink>
          </>
        }
        aside={
          <SpotlightCard>
            <BrainCircuit className="h-6 w-6 text-cyan-200" />
            <h3 className="mt-5 font-display text-2xl text-white">Model choice stays in your hands</h3>
            <p className="mt-3 text-sm leading-7 text-white/58">Bring-your-own provider keys and preferred workspace providers are part of the visual story, not buried in settings.</p>
          </SpotlightCard>
        }
      />

      <MotionSection className="section-shell pt-16 sm:pt-20" delay={0.06}>
        <SectionHeading
          eyebrow="Technology layers"
          title="A modern system should communicate how it thinks"
          description="This stack is framed around signals, AI coordination, governance, and composable rollout paths instead of vague platform language."
        />
        <div className="mt-10 grid gap-4 xl:grid-cols-4">
          {technologyLayers.map((layer) => (
            <SpotlightCard key={layer.title}>
              <layer.icon className="h-6 w-6 text-cyan-200" />
              <h3 className="mt-5 font-display text-2xl text-white">{layer.title}</h3>
              <p className="mt-3 text-sm leading-7 text-white/58">{layer.description}</p>
              <p className="mt-5 text-sm leading-7 text-white/42">{layer.detail}</p>
            </SpotlightCard>
          ))}
        </div>
      </MotionSection>

      <MotionSection className="section-shell pt-16 sm:pt-20" delay={0.08}>
        <div className="grid gap-4 lg:grid-cols-[0.92fr_1.08fr]">
          <SpotlightCard className="min-h-[420px]">
            <p className="kicker">Intelligence pattern</p>
            <h3 className="mt-4 font-display text-3xl text-white">Detect. Decide. Act. Govern.</h3>
            <div className="mt-8 space-y-4">
              {[
                { icon: Radar, title: 'Detect', detail: 'Route drift, inventory pressure, and workspace risk enter the same command narrative.' },
                { icon: Cpu, title: 'Decide', detail: 'Route choices, costs, and launch readiness stay in view while the operator acts.' },
                { icon: Cable, title: 'Act', detail: 'Shipments, alerts, and desktop flows stay operationally linked instead of conceptually linked.' },
                { icon: Fingerprint, title: 'Govern', detail: 'Audit events, provider changes, and commercial posture remain reviewable.' },
              ].map((item) => (
                <div key={item.title} className="rounded-[20px] border border-white/10 bg-black/25 p-4">
                  <div className="flex items-center gap-3">
                    <item.icon className="h-5 w-5 text-cyan-200" />
                    <h4 className="font-display text-xl text-white">{item.title}</h4>
                  </div>
                  <p className="mt-3 text-sm leading-7 text-white/58">{item.detail}</p>
                </div>
              ))}
            </div>
          </SpotlightCard>

          <div className="glass-panel overflow-hidden rounded-[34px] px-6 py-6">
            <div className="flex items-center justify-between gap-4">
              <div>
                <p className="kicker">Illustrative logic</p>
                <h3 className="mt-4 font-display text-3xl text-white">The AI layer should read like a system, not a slogan</h3>
              </div>
              <div className="pill">
                <ShieldCheck className="h-4 w-4" />
                governed flow
              </div>
            </div>

            <div className="mt-8 overflow-hidden rounded-[28px] border border-white/10 bg-black/45">
              <div className="flex items-center justify-between border-b border-white/10 px-4 py-3 text-xs uppercase tracking-[0.18em] text-white/42">
                <span>freightpilot.logic.ts</span>
                <span className="inline-flex items-center gap-2">
                  live orchestration <ArrowRight className="h-3.5 w-3.5" />
                </span>
              </div>
              <pre className="overflow-x-auto px-4 py-5 text-sm leading-7 text-cyan-100/88">
                <code>{codeSnippet}</code>
              </pre>
            </div>

            <div className="mt-6 flex flex-wrap gap-2">
              {trustRibbon.map((item) => (
                <span key={item} className="rounded-full border border-white/10 bg-white/[0.05] px-3 py-2 text-xs text-white/56">
                  {item}
                </span>
              ))}
            </div>
          </div>
        </div>
      </MotionSection>
    </>
  );
}
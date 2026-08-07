import type { Metadata } from 'next';
import { ArrowRight, BrainCircuit, Cable, Cpu, Fingerprint, Radar, ShieldCheck } from 'lucide-react';

import { MagneticLink } from '@/components/site/magnetic-link';
import { MotionSection } from '@/components/site/motion-section';
import { PageHero } from '@/components/site/page-hero';
import { SectionHeading } from '@/components/site/section-heading';
import { SpotlightCard } from '@/components/site/spotlight-card';
import { codeSnippet, startFreeCta, technologyLayers, trustRibbon } from '@/lib/site-content';

export const metadata: Metadata = {
  title: 'Technology',
  description:
    'Learn how FreightPilot handles AI provider controls, signal processing, governance, and decision support with full audit history and workspace policy visibility.',
};

const layerIconColors = ['text-cyan-200', 'text-violet-300', 'text-amber-200', 'text-emerald-200'];

export default function TechnologyPage() {
  return (
    <>
      <PageHero
        eyebrow="Technology"
        title="AI assistance with visible controls and audit history"
        description="FreightPilot treats signal handling, model routing, workspace policy, and auditability as operational controls that need to stay visible to the team."
        actions={
          <MagneticLink href="/launch" variant="primary">
            {startFreeCta}
          </MagneticLink>
        }
        aside={
          <SpotlightCard>
            <BrainCircuit className="h-6 w-6 text-violet-300" />
            <h3 className="mt-5 font-display text-2xl text-white">Model choice stays in your hands</h3>
            <p className="mt-3 text-sm leading-7 text-white/60">Bring-your-own provider keys and preferred workspace providers are part of the visual story, not buried in settings.</p>
          </SpotlightCard>
        }
      />

      <MotionSection className="section-shell pt-16 sm:pt-20" delay={0.06}>
        <SectionHeading
          eyebrow="Technology layers"
          title="The stack should explain how decisions are supported"
          description="The technology model is organized around live signal, provider control, governance, and rollout support instead of generic AI language."
        />
        <div className="mt-10 grid gap-4 xl:grid-cols-4">
          {technologyLayers.map((layer, index) => (
            <SpotlightCard key={layer.title}>
              <layer.icon className={`h-6 w-6 ${layerIconColors[index % layerIconColors.length]}`} />
              <h3 className="mt-5 font-display text-2xl text-white">{layer.title}</h3>
              <p className="mt-3 text-sm leading-7 text-white/60">{layer.description}</p>
              <p className="mt-5 text-sm leading-7 text-white/50">{layer.detail}</p>
            </SpotlightCard>
          ))}
        </div>
      </MotionSection>

      <MotionSection className="section-shell pt-16 sm:pt-20" delay={0.06}>
        <div className="grid gap-4 lg:grid-cols-[0.92fr_1.08fr]">
          <SpotlightCard className="min-h-[420px]">
            <p className="kicker">Intelligence pattern</p>
            <h3 className="mt-4 font-display text-3xl text-white">Detect. Decide. Act. Govern.</h3>
            <div className="mt-8 space-y-4">
              {[
                { icon: Radar, title: 'Detect', detail: 'Route drift, inventory pressure, and workspace risk enter the same command narrative.', color: 'text-cyan-200' },
                { icon: Cpu, title: 'Decide', detail: 'Route choices, costs, and launch readiness stay in view while the operator acts.', color: 'text-violet-300' },
                { icon: Cable, title: 'Act', detail: 'Shipments, alerts, and desktop flows stay operationally linked instead of conceptually linked.', color: 'text-amber-200' },
                { icon: Fingerprint, title: 'Govern', detail: 'Audit events, provider changes, and commercial posture remain reviewable.', color: 'text-emerald-200' },
              ].map((item) => (
                <div key={item.title} className="rounded-[20px] border border-white/10 bg-black/25 p-4">
                  <div className="flex items-center gap-3">
                    <item.icon className={`h-5 w-5 ${item.color}`} />
                    <h4 className="font-display text-xl text-white">{item.title}</h4>
                  </div>
                  <p className="mt-3 text-sm leading-7 text-white/60">{item.detail}</p>
                </div>
              ))}
            </div>
          </SpotlightCard>

          <div className="glass-panel overflow-hidden px-6 py-6">
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
              <div className="flex items-center justify-between border-b border-white/10 px-4 py-3 text-xs uppercase tracking-[0.18em] text-white/50">
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
                <span key={item} className="rounded-full border border-white/10 bg-white/[0.05] px-3 py-2 text-xs text-white/60">
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
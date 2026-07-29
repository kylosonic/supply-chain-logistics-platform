'use client';

import { motion } from 'framer-motion';
import { ArrowUpRight, BrainCircuit, ChartNoAxesCombined, ShieldCheck, Sparkles } from 'lucide-react';

import { SpotlightCard } from './spotlight-card';

const particles = Array.from({ length: 10 }, (_, index) => ({
  id: index,
  left: `${8 + ((index * 11) % 78)}%`,
  top: `${6 + ((index * 17) % 82)}%`,
  delay: index * 0.18,
  duration: 6 + (index % 4),
}));

const commandStats = [
  ['Open exceptions', '03', 'Require dispatcher review'],
  ['At-risk lanes', '02', 'Crossing margin threshold'],
  ['Launch readiness', '82%', 'Checks nearly complete'],
] as const;

const rhythmSteps = ['Review the exception queue', 'Compare route options', 'Record the action and handoff'] as const;

const liveFeedItems = [
  ['Shipment SH-402', 'Delivery window drifting by 27 minutes'],
  ['Item AX-14', 'Safety stock is low in West Hub'],
  ['Route 7', 'Capacity threshold exceeded'],
] as const;

export function HeroScene() {
  return (
    <div className="relative isolate overflow-hidden rounded-[32px] border border-white/10 bg-white/[0.04] p-4 shadow-luxe sm:p-5 lg:min-h-[500px] xl:min-h-[540px] xl:p-6">
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_top_right,rgba(96,165,250,0.24),transparent_28%),radial-gradient(circle_at_bottom_left,rgba(34,211,238,0.16),transparent_30%),linear-gradient(180deg,rgba(255,255,255,0.04),rgba(255,255,255,0.01))]" />
      <div className="absolute inset-0 bg-[linear-gradient(rgba(255,255,255,0.05)_1px,transparent_1px),linear-gradient(90deg,rgba(255,255,255,0.05)_1px,transparent_1px)] bg-[size:34px_34px] opacity-20" />

      {particles.map((particle) => (
        <motion.span
          key={particle.id}
          className={`absolute h-1.5 w-1.5 rounded-full bg-cyan-200/60 shadow-[0_0_18px_rgba(103,232,249,0.7)] ${particle.id > 5 ? 'hidden lg:block' : ''}`}
          style={{ left: particle.left, top: particle.top }}
          animate={{ y: [0, -18, 0], opacity: [0.3, 1, 0.4] }}
          transition={{ duration: particle.duration, repeat: Infinity, ease: 'easeInOut', delay: particle.delay }}
        />
      ))}

      <div className="relative z-10 lg:hidden">
        <div className="flex flex-col gap-4">
          <div className="flex flex-col items-start gap-3 sm:flex-row sm:items-center sm:justify-between">
            <div className="inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/[0.04] px-3 py-2 text-[11px] uppercase tracking-[0.22em] text-white/70">
              <Sparkles className="h-4 w-4" />
              Live workspace overview
            </div>
            <div className="inline-flex items-center gap-2 rounded-full border border-cyan-400/20 bg-cyan-400/10 px-3 py-2 text-xs text-cyan-100">
              <ShieldCheck className="h-4 w-4" />
              Governance enabled
            </div>
          </div>

          <motion.div
            initial={{ opacity: 0, y: 18, scale: 0.98 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            transition={{ duration: 0.75, ease: [0.16, 1, 0.3, 1] }}
            className="glass-panel overflow-hidden rounded-[28px] border border-white/10 px-4 py-4"
          >
            <div className="flex flex-col gap-4">
              <div className="flex flex-col gap-3">
                <div>
                  <p className="text-xs uppercase tracking-[0.2em] text-white/45">Operations summary</p>
                  <h3 className="balanced-headline mt-3 max-w-[8ch] font-display text-[clamp(2rem,10vw,2.7rem)] leading-[0.95] text-white">
                    Control overview
                  </h3>
                </div>
                <div className="inline-flex w-fit items-center gap-2 rounded-full border border-violet-400/20 bg-violet-400/10 px-3 py-2 text-xs text-violet-100">
                  <BrainCircuit className="h-4 w-4" />
                  Assisted decisions
                </div>
              </div>

              <div className="grid gap-3 sm:grid-cols-3">
                {commandStats.map(([title, value, detail]) => (
                  <div key={title} className="rounded-[20px] border border-white/10 bg-black/30 p-3">
                    <p className="text-[11px] uppercase tracking-[0.18em] text-white/45">{title}</p>
                    <p className="mt-2 font-display text-[clamp(1.8rem,6vw,2.4rem)] leading-none text-white">{value}</p>
                    <p className="mt-2 text-sm leading-6 text-white/55">{detail}</p>
                  </div>
                ))}
              </div>

              <div className="rounded-[24px] border border-white/10 bg-black/35 p-4">
                <div className="flex items-center justify-between text-white/65">
                  <span className="text-xs uppercase tracking-[0.18em]">Recommended actions</span>
                  <ArrowUpRight className="h-4 w-4" />
                </div>
                <div className="mt-4 grid gap-3 sm:grid-cols-3">
                  {rhythmSteps.map((item, index) => (
                    <div key={item} className="rounded-[18px] border border-white/10 bg-white/[0.03] p-3">
                      <span className="text-xs text-cyan-200/80">0{index + 1}</span>
                      <p className="mt-2 text-sm text-white">{item}</p>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </motion.div>

          <div className="grid gap-4">
            <SpotlightCard className="min-h-0">
              <div className="flex items-center justify-between gap-3 text-white/75">
                <span className="text-xs uppercase tracking-[0.2em]">Live alerts</span>
                <ChartNoAxesCombined className="h-4 w-4" />
              </div>
              <div className="mt-4 space-y-3">
                {liveFeedItems.slice(0, 2).map(([title, detail]) => (
                  <div key={title} className="rounded-[18px] border border-white/10 bg-black/30 px-4 py-3">
                    <p className="text-sm font-semibold text-white">{title}</p>
                    <p className="mt-1 text-xs text-white/55">{detail}</p>
                  </div>
                ))}
              </div>
            </SpotlightCard>

            <SpotlightCard className="min-h-0">
              <p className="text-xs uppercase tracking-[0.2em] text-white/45">Workspace controls</p>
              <div className="mt-4 grid gap-4 sm:grid-cols-2">
                <div>
                  <p className="balanced-headline max-w-[7ch] font-display text-[clamp(1.7rem,8vw,2.1rem)] leading-[1] text-white">
                    Launch checklist
                  </p>
                  <p className="mt-2 text-sm leading-7 text-white/60">
                    Confirm users, devices, and integrations before opening the team to live work.
                  </p>
                </div>
                <div>
                  <p className="balanced-headline max-w-[7ch] font-display text-[clamp(1.7rem,8vw,2.1rem)] leading-[1] text-white">
                    Provider controls
                  </p>
                  <p className="mt-2 text-sm leading-7 text-white/60">
                    Choose approved providers and keep key ownership inside the workspace.
                  </p>
                </div>
              </div>
            </SpotlightCard>
          </div>
        </div>
      </div>

      <div className="relative z-10 hidden h-full gap-4 sm:gap-5 lg:grid lg:grid-rows-[auto_1fr_auto]">
        <div className="flex flex-col items-start gap-3 sm:flex-row sm:items-center sm:justify-between">
          <div className="inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/[0.04] px-3 py-2 text-xs uppercase tracking-[0.22em] text-white/70">
            <Sparkles className="h-4 w-4" />
            Live workspace overview
          </div>
          <div className="inline-flex items-center gap-2 rounded-full border border-cyan-400/20 bg-cyan-400/10 px-3 py-2 text-xs text-cyan-100">
            <ShieldCheck className="h-4 w-4" />
            Governance enabled
          </div>
        </div>

        <div className="grid gap-4 xl:grid-cols-[0.94fr_1.06fr]">
          <motion.div
            initial={{ opacity: 0, y: 24, scale: 0.97 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            transition={{ duration: 0.9, ease: [0.16, 1, 0.3, 1] }}
            className="glass-panel overflow-hidden rounded-[28px] border border-white/10 px-4 py-4 sm:px-5 sm:py-5"
          >
            <div className="flex flex-col gap-3 2xl:flex-row 2xl:items-center 2xl:justify-between">
              <div>
                <p className="text-xs uppercase tracking-[0.2em] text-white/45">Operations summary</p>
                <h3 className="balanced-headline mt-3 max-w-[9ch] font-display text-[clamp(1.9rem,2.6vw,2.25rem)] leading-[0.98] text-white">Control overview</h3>
              </div>
              <div className="inline-flex w-fit items-center gap-2 rounded-full border border-violet-400/20 bg-violet-400/10 px-3 py-2 text-xs text-violet-100">
                <BrainCircuit className="h-4 w-4" />
                Assisted decisions
              </div>
            </div>

            <div className="mt-6 grid gap-3 sm:grid-cols-2 2xl:grid-cols-3 [&>*:last-child]:sm:col-span-2 [&>*:last-child]:2xl:col-span-1">
              {commandStats.map(([title, value, detail]) => (
                <div key={title} className="rounded-[22px] border border-white/10 bg-black/30 p-4">
                  <p className="text-xs uppercase tracking-[0.18em] text-white/45">{title}</p>
                  <p className="mt-3 font-display text-3xl text-white">{value}</p>
                  <p className="mt-2 text-sm text-white/55">{detail}</p>
                </div>
              ))}
            </div>

            <div className="mt-5 rounded-[24px] border border-white/10 bg-black/35 p-4">
              <div className="flex items-center justify-between text-white/65">
                <span className="text-xs uppercase tracking-[0.18em]">Recommended actions</span>
                <ArrowUpRight className="h-4 w-4" />
              </div>
              <div className="mt-4 grid gap-3 sm:grid-cols-2 [&>*:last-child]:sm:col-span-2">
                {rhythmSteps.map((item, index) => (
                  <div key={item} className="rounded-[18px] border border-white/10 bg-white/[0.03] p-3">
                    <span className="text-xs text-cyan-200/80">0{index + 1}</span>
                    <p className="mt-2 text-sm leading-6 text-white">{item}</p>
                  </div>
                ))}
              </div>
            </div>
          </motion.div>

          <div className="grid gap-4">
            <motion.div
              initial={{ opacity: 0, y: 18 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.8, delay: 0.15 }}
            >
              <SpotlightCard className="min-h-[210px]">
                <div className="flex items-center justify-between gap-3 text-white/75">
                  <span className="text-xs uppercase tracking-[0.2em]">Live alerts</span>
                  <ChartNoAxesCombined className="h-4 w-4" />
                </div>
                <div className="mt-4 space-y-3">
                  {liveFeedItems.map(([title, detail]) => (
                    <div key={title} className="rounded-[18px] border border-white/10 bg-black/30 px-4 py-3">
                      <p className="text-sm font-semibold text-white">{title}</p>
                      <p className="mt-1 text-xs text-white/55">{detail}</p>
                    </div>
                  ))}
                </div>
              </SpotlightCard>
            </motion.div>

            <motion.div
              initial={{ opacity: 0, y: 18 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.8, delay: 0.28 }}
              className="grid gap-4 2xl:grid-cols-2"
            >
              <SpotlightCard>
                <p className="text-xs uppercase tracking-[0.2em] text-white/45">Launch workspace</p>
                <p className="balanced-headline mt-4 max-w-[10ch] font-display text-[clamp(1.55rem,2.2vw,1.9rem)] leading-[1.02] text-white">Launch checklist</p>
                <p className="mt-2 text-sm leading-7 text-white/60">Track approvals, environment checks, and go-live readiness in one flow.</p>
              </SpotlightCard>
              <SpotlightCard>
                <p className="text-xs uppercase tracking-[0.2em] text-white/45">Provider controls</p>
                <p className="balanced-headline mt-4 max-w-[10ch] font-display text-[clamp(1.55rem,2.2vw,1.9rem)] leading-[1.02] text-white">Approved models</p>
                <p className="mt-2 text-sm leading-7 text-white/60">Choose preferred providers without giving up workspace policy and audit history.</p>
              </SpotlightCard>
            </motion.div>
          </div>
        </div>

        <div className="flex flex-col items-start gap-2 rounded-[24px] border border-white/10 bg-black/30 px-4 py-4 text-sm text-white/65 sm:flex-row sm:items-center sm:justify-between">
          <span>Explore how the platform handles planning, response, launch, and governance.</span>
          <motion.span animate={{ y: [0, 8, 0] }} transition={{ duration: 1.8, repeat: Infinity }}>
            ↓
          </motion.span>
        </div>
      </div>
    </div>
  );
}
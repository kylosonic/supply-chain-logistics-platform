'use client';

import { useState } from 'react';
import { Minus, Plus, Route, UploadCloud, UserPlus } from 'lucide-react';

import {
  hideLabel,
  howItWorksHeading,
  howItWorksSteps,
  showLabel,
} from '@/lib/site-content';

const stepIcons = [UserPlus, Route, UploadCloud];

/**
 * Collapsed-by-default "How it works" section (NB-38).
 *
 * Expansion is a CSS grid-rows reveal (`how-it-works-reveal` keyframe in
 * globals.css) — deliberately NOT framer-motion, so the home page keeps its
 * single allowed entrance animation (the hero `m.h1`).
 */
export function HowItWorks() {
  const [open, setOpen] = useState(false);

  return (
    <section className="section-shell pt-14 sm:pt-18" data-section="how-it-works">
      <div className="glass-panel rounded-[38px] px-6 py-8 sm:px-8">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <h2 className="max-w-[24ch] font-display text-[clamp(1.75rem,3.6vw,2.9rem)] leading-[0.98] tracking-[-0.02em] text-white">
            {howItWorksHeading}
          </h2>
          <button
            type="button"
            onClick={() => setOpen((current) => !current)}
            aria-expanded={open}
            aria-controls="how-it-works-steps"
            className="inline-flex min-h-12 items-center justify-center gap-2 self-start rounded-full border border-white/15 bg-white/[0.06] px-5 text-sm font-semibold text-white transition hover:bg-white/[0.1] sm:self-auto"
          >
            {open ? <Minus className="h-4 w-4" aria-hidden="true" /> : <Plus className="h-4 w-4" aria-hidden="true" />}
            {open ? hideLabel : showLabel}
          </button>
        </div>

        {open ? (
          <div className="how-it-works-reveal mt-8">
            <ol id="how-it-works-steps" className="min-h-0 space-y-4 overflow-hidden" role="list">
              {howItWorksSteps.map((step, index) => {
                const Icon = stepIcons[index % stepIcons.length];
                return (
                  <li
                    key={step}
                    className="flex items-start gap-4 rounded-[24px] border border-white/10 bg-black/25 p-5"
                  >
                    <span className="inline-flex h-9 w-9 shrink-0 items-center justify-center rounded-full border border-white/10 bg-white/[0.05]">
                      <Icon className="h-4 w-4 text-cyan-200" aria-hidden="true" />
                    </span>
                    <span className="text-sm leading-7 text-white/72 sm:text-base">{step}</span>
                  </li>
                );
              })}
            </ol>
          </div>
        ) : null}
      </div>
    </section>
  );
}

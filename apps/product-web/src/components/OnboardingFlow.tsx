'use client';

import React, { useState } from 'react';
import { ONBOARDING_CONFIGS, MarketSegment } from '../lib/onboarding-config';

export function OnboardingFlow() {
  const [segment, setSegment] = useState<MarketSegment>('mid-market');
  const [currentStepIndex, setCurrentStepIndex] = useState(0);

  const config = ONBOARDING_CONFIGS[segment];
  const steps = config.steps;
  const currentStep = steps[currentStepIndex];

  return (
    <div className="max-w-3xl mx-auto p-6 space-y-8 bg-slate-900 text-slate-100 rounded-xl shadow-2xl">
      <div className="space-y-4">
        <h1 className="text-3xl font-bold font-['Space_Grotesk'] text-slate-50">Setup your workspace</h1>
        <p className="text-slate-400">Select your operational profile to tailor the onboarding experience.</p>
        
        <div className="flex gap-4">
          <button
            onClick={() => { setSegment('mid-market'); setCurrentStepIndex(0); }}
            className={`px-4 py-2 rounded-lg font-semibold transition ${segment === 'mid-market' ? 'bg-emerald-600 text-white' : 'bg-slate-800 text-slate-300 hover:bg-slate-700'}`}
          >
            Mid-Market
          </button>
          <button
            onClick={() => { setSegment('local-network'); setCurrentStepIndex(0); }}
            className={`px-4 py-2 rounded-lg font-semibold transition ${segment === 'local-network' ? 'bg-emerald-600 text-white' : 'bg-slate-800 text-slate-300 hover:bg-slate-700'}`}
          >
            Local Network
          </button>
        </div>
      </div>

      <div className="border border-slate-800 rounded-lg p-6 bg-slate-800/50 space-y-6">
        <div className="flex items-center justify-between mb-4">
          <span className="text-sm font-semibold tracking-wider text-slate-400 uppercase">
            Step {currentStepIndex + 1} of {steps.length}
          </span>
          <span className="text-sm text-emerald-400 font-medium">
            {config.displayName}
          </span>
        </div>

        <div className="space-y-2">
          <h2 className="text-2xl font-semibold text-slate-50">{currentStep.title}</h2>
          <p className="text-slate-400">{currentStep.description}</p>
        </div>

        <div className="pt-8 flex justify-between">
          <button
            disabled={currentStepIndex === 0}
            onClick={() => setCurrentStepIndex((i) => Math.max(0, i - 1))}
            className="px-6 py-2 rounded-lg font-medium text-slate-300 hover:bg-slate-800 disabled:opacity-50 disabled:cursor-not-allowed transition"
          >
            Back
          </button>
          <button
            onClick={() => setCurrentStepIndex((i) => Math.min(steps.length - 1, i + 1))}
            disabled={currentStepIndex === steps.length - 1}
            className="px-6 py-2 rounded-lg font-medium bg-emerald-600 hover:bg-emerald-500 text-white disabled:opacity-50 disabled:cursor-not-allowed transition shadow-[0_0_15px_rgba(5,150,105,0.4)]"
          >
            {currentStepIndex === steps.length - 1 ? 'Finish Setup' : 'Continue'}
          </button>
        </div>
      </div>
    </div>
  );
}

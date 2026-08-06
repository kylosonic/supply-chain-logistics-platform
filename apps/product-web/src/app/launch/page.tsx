import type { Metadata } from 'next';

import { PageHero } from '@/components/site/page-hero';
import { SectionHeading } from '@/components/site/section-heading';
import { SignupForm } from '@/components/site/signup-form';
import { afterSignupSteps } from '@/lib/site-content';

export const metadata: Metadata = {
  title: 'Launch',
  description:
    'Sign up and your workspace loads with sample data. Run your first route optimization in minutes — no card required.',
};

export default function LaunchPage() {
  return (
    <>
      <PageHero
        eyebrow="Launch"
        title="Start your workspace with sample data"
        description="Sign up and your workspace loads with sample data — warehouses, fleet, inventory, orders, all ready. Optimize your first route immediately. No card required."
      />

      <section className="section-shell pt-16 sm:pt-20">
        <div className="grid gap-4 lg:grid-cols-[1.02fr_0.98fr]">
          <SignupForm />

          <div className="glass-panel rounded-[34px] px-6 py-7">
            <SectionHeading
              eyebrow="After signup"
              title="What happens next"
              description="Three steps from signup to your first optimized route."
            />
            <div className="mt-8 space-y-4">
              {afterSignupSteps.map((step) => (
                <div key={step.title} className="rounded-[24px] border border-white/10 bg-black/25 p-5">
                  <span className="kicker">{step.label}</span>
                  <h3 className="mt-3 font-display text-2xl text-white">{step.title}</h3>
                  <p className="mt-3 text-sm leading-7 text-white/60">{step.detail}</p>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>
    </>
  );
}

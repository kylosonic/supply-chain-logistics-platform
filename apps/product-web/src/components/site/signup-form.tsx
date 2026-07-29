'use client';

import { useState } from 'react';
import { zodResolver } from '@hookform/resolvers/zod';
import { LoaderCircle, ShieldCheck, Sparkles } from 'lucide-react';
import { useForm } from 'react-hook-form';
import { z } from 'zod';

import { companySignup, type SignupTier } from '@/lib/company-signup';
import { cn } from '@/lib/cn';

const launchSchema = z.object({
  company_name: z.string().min(2, 'Enter your company name.'),
  company_email: z.string().email('Use a valid company email.'),
  full_name: z.string().min(2, 'Enter your full name.'),
  password: z.string().min(8, 'Use at least 8 characters.'),
  subscription_tier: z.enum(['starter', 'scale', 'enterprise']),
});

type LaunchValues = z.infer<typeof launchSchema>;

const launchOptions: Array<{ value: SignupTier; label: string; detail: string }> = [
  { value: 'starter', label: 'Starter', detail: 'Single-region launch teams' },
  { value: 'scale', label: 'Scale', detail: 'Multi-region operations' },
  { value: 'enterprise', label: 'Enterprise', detail: 'Transformation programs' },
];

const fieldClassName =
  'peer min-h-14 w-full rounded-[22px] border border-white/10 bg-black/35 px-4 pb-3 pt-6 text-sm text-white outline-none transition placeholder:text-transparent focus:border-cyan-300/50';

export function SignupForm() {
  const [statusMessage, setStatusMessage] = useState<string | null>(null);
  const [statusTone, setStatusTone] = useState<'success' | 'error' | null>(null);

  const {
    register,
    handleSubmit,
    watch,
    formState: { errors, isSubmitting },
    reset,
  } = useForm<LaunchValues>({
    resolver: zodResolver(launchSchema),
    defaultValues: {
      subscription_tier: 'scale',
    },
  });

  const activeTier = watch('subscription_tier');

  const onSubmit = handleSubmit(async (values) => {
    setStatusMessage(null);
    setStatusTone(null);

    try {
      const result = await companySignup(values);
      setStatusTone('success');
      setStatusMessage(
        result.email_verification_required
          ? 'Workspace created. Verify the email, then continue into the desktop launch workstation.'
          : 'Workspace created. Your rollout team can move directly into launch readiness.',
      );
      reset({
        company_name: '',
        company_email: '',
        full_name: '',
        password: '',
        subscription_tier: values.subscription_tier,
      });
    } catch (error) {
      setStatusTone('error');
      setStatusMessage(error instanceof Error ? error.message : 'Could not create the company workspace.');
    }
  });

  return (
    <div className="glass-panel overflow-hidden rounded-[32px] px-6 py-6">
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="kicker">Launch workspace</p>
          <h2 className="mt-4 font-display text-3xl text-white">Create the company command space</h2>
        </div>
        <span className="inline-flex items-center gap-2 rounded-full border border-cyan-300/20 bg-cyan-300/10 px-3 py-2 text-xs text-cyan-100">
          <ShieldCheck className="h-4 w-4" />
          Secure onboarding
        </span>
      </div>

      <form className="mt-6 space-y-5" onSubmit={onSubmit}>
        <div className="grid gap-4 md:grid-cols-2">
          <Field label="Company name" error={errors.company_name?.message}>
            <input className={fieldClassName} placeholder="Company name" {...register('company_name')} />
          </Field>
          <Field label="Launch owner" error={errors.full_name?.message}>
            <input className={fieldClassName} placeholder="Launch owner" {...register('full_name')} />
          </Field>
        </div>

        <div className="grid gap-4 md:grid-cols-2">
          <Field label="Company email" error={errors.company_email?.message}>
            <input className={fieldClassName} placeholder="Company email" type="email" {...register('company_email')} />
          </Field>
          <Field label="Password" error={errors.password?.message}>
            <input className={fieldClassName} placeholder="Password" type="password" {...register('password')} />
          </Field>
        </div>

        <div className="space-y-3">
          <p className="text-xs font-semibold uppercase tracking-[0.2em] text-white/48">Subscription tier</p>
          <div className="grid gap-3 md:grid-cols-3">
            {launchOptions.map((option) => (
              <label
                key={option.value}
                className={cn(
                  'cursor-pointer rounded-[24px] border px-4 py-4 transition',
                  activeTier === option.value ? 'border-cyan-300/40 bg-cyan-300/10 text-white' : 'border-white/10 bg-white/[0.03] text-white/68',
                )}
              >
                <input type="radio" value={option.value} className="sr-only" {...register('subscription_tier')} />
                <span className="block font-display text-lg">{option.label}</span>
                <span className="mt-1 block text-sm">{option.detail}</span>
              </label>
            ))}
          </div>
        </div>

        <button
          type="submit"
          disabled={isSubmitting}
          className="group inline-flex min-h-14 w-full items-center justify-center gap-2 rounded-full bg-gradient-to-r from-sky-400 via-cyan-300 to-violet-300 px-5 text-sm font-semibold text-slate-950 shadow-[0_18px_60px_rgba(56,189,248,0.28)] transition hover:brightness-105 disabled:cursor-not-allowed disabled:opacity-60"
        >
          {isSubmitting ? <LoaderCircle className="h-4 w-4 animate-spin" /> : <Sparkles className="h-4 w-4" />}
          {isSubmitting ? 'Creating workspace...' : 'Create company workspace'}
        </button>

        {statusMessage ? (
          <div
            className={cn(
              'rounded-[22px] border px-4 py-4 text-sm leading-7',
              statusTone === 'success'
                ? 'border-emerald-400/25 bg-emerald-400/10 text-emerald-100'
                : 'border-rose-400/25 bg-rose-400/10 text-rose-100',
            )}
          >
            {statusMessage}
          </div>
        ) : null}
      </form>
    </div>
  );
}

function Field({
  children,
  label,
  error,
}: {
  children: React.ReactNode;
  label: string;
  error?: string;
}) {
  return (
    <label className="relative block">
      {children}
      <span className="pointer-events-none absolute left-4 top-3 text-[11px] font-semibold uppercase tracking-[0.18em] text-white/42 transition peer-focus:text-cyan-200/80">
        {label}
      </span>
      {error ? <span className="mt-2 block text-xs text-rose-300">{error}</span> : null}
    </label>
  );
}
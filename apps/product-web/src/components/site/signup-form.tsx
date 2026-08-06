'use client';

import { useState } from 'react';
import { zodResolver } from '@hookform/resolvers/zod';
import { LoaderCircle } from 'lucide-react';
import { useForm } from 'react-hook-form';
import { z } from 'zod';

import { companySignup, type SignupTier } from '@/lib/company-signup';
import { cn } from '@/lib/cn';
import {
  externalLinks,
  signupFormNote,
  signupFormSubline,
  signupSuccessMessage,
} from '@/lib/site-content';

// react-hook-form reports an unchecked radio group as null (or '') — accept
// both, then normalize to undefined so the unset tier is truly optional
// (blueprint §1.10).
const launchSchema = z.object({
  company_name: z.string().min(2, 'Enter your company name.'),
  company_email: z.string().email('Use a valid company email.'),
  full_name: z.string().optional(),
  password: z.string().min(8, 'Use at least 8 characters.'),
  subscription_tier: z
    .union([z.enum(['starter', 'scale', 'enterprise']), z.literal(''), z.null()])
    .optional()
    .transform((value) => (value === '' || value === null ? undefined : value)),
});

type LaunchInput = z.input<typeof launchSchema>;
type LaunchValues = z.output<typeof launchSchema>;

const launchOptions: Array<{ value: SignupTier; label: string }> = [
  { value: 'starter', label: 'Starter — 4,500 ETB/month' },
  { value: 'scale', label: 'Scale — 10,000 ETB/quarter' },
  { value: 'enterprise', label: 'Enterprise — 45,000 ETB/quarter' },
];

const fieldClassName =
  'peer min-h-14 w-full rounded-[22px] border border-white/10 bg-black/35 px-4 pb-3 pt-6 text-base text-white outline-none transition placeholder:text-white/25 focus:border-cyan-300/50 sm:text-sm';

export function SignupForm() {
  const [statusMessage, setStatusMessage] = useState<string | null>(null);
  const [statusTone, setStatusTone] = useState<'success' | 'error' | null>(null);

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<LaunchInput, unknown, LaunchValues>({
    resolver: zodResolver(launchSchema),
  });

  const onSubmit = handleSubmit(async (values) => {
    setStatusMessage(null);
    setStatusTone(null);

    try {
      await companySignup({
        company_name: values.company_name,
        company_email: values.company_email,
        password: values.password,
        ...(values.full_name ? { full_name: values.full_name } : {}),
        ...(values.subscription_tier ? { subscription_tier: values.subscription_tier } : {}),
      });

      setStatusTone('success');
      setStatusMessage(signupSuccessMessage);
      // The ops console bootstraps the session from the supply_chain_token
      // cookie (AuthContext → /auth/me → /); same-site it lands on the
      // workspace, otherwise on its existing /login.
      window.location.assign(externalLinks.console);
    } catch (error) {
      setStatusTone('error');
      setStatusMessage(error instanceof Error ? error.message : 'Could not create the company workspace.');
    }
  });

  return (
    <div className="glass-panel overflow-hidden rounded-[32px] px-5 py-5 sm:px-6 sm:py-6">
      <div>
        <p className="kicker">Launch</p>
        <h2 className="mt-4 font-display text-3xl text-white">Start free</h2>
        <p className="mt-2 text-sm leading-7 text-white/68">{signupFormSubline}</p>
        <p className="mt-1 text-xs text-white/50">{signupFormNote}</p>
      </div>

      {/* noValidate: the zod schema is the single validation source
          (native constraint validation would block jsdom submissions). */}
      <form className="mt-6 space-y-5" onSubmit={onSubmit} noValidate>
        <div className="grid gap-4 sm:grid-cols-2">
          <Field label="Company name" error={errors.company_name?.message}>
            <input className={fieldClassName} placeholder="Company name" {...register('company_name')} />
          </Field>
          <Field label="Full name (optional)" error={errors.full_name?.message}>
            <input className={fieldClassName} placeholder="Full name (optional)" {...register('full_name')} />
          </Field>
        </div>

        <div className="grid gap-4 sm:grid-cols-2">
          <Field label="Company email" error={errors.company_email?.message}>
            <input className={fieldClassName} placeholder="Company email" type="email" {...register('company_email')} />
          </Field>
          <Field label="Password" error={errors.password?.message}>
            <input className={fieldClassName} placeholder="Password" type="password" {...register('password')} />
          </Field>
        </div>

        <div className="space-y-3">
          <p className="text-xs font-semibold uppercase tracking-[0.2em] text-white/48">
            Tier <span className="normal-case text-white/38">— Optional — choose a tier later inside your workspace.</span>
          </p>
          <div className="grid gap-3 lg:grid-cols-3">
            {launchOptions.map((option) => (
              <label
                key={option.value}
                className="cursor-pointer rounded-[24px] border border-white/10 bg-white/[0.03] px-4 py-4 text-sm text-white/68 transition has-[:checked]:border-cyan-300/40 has-[:checked]:bg-cyan-300/10 has-[:checked]:text-white"
              >
                <input type="radio" value={option.value} className="sr-only" {...register('subscription_tier')} />
                <span className="block">{option.label}</span>
              </label>
            ))}
          </div>
        </div>

        <button
          type="submit"
          disabled={isSubmitting}
          className="group inline-flex min-h-14 w-full items-center justify-center gap-2 rounded-full bg-gradient-to-r from-sky-400 via-cyan-300 to-violet-300 px-5 text-sm font-semibold text-slate-950 shadow-[0_18px_60px_rgba(56,189,248,0.28)] transition hover:brightness-105 disabled:cursor-not-allowed disabled:opacity-60"
        >
          {isSubmitting ? <LoaderCircle className="h-4 w-4 animate-spin" /> : null}
          {isSubmitting ? 'Creating workspace...' : 'Start free'}
        </button>

        {statusMessage ? (
          <div
            role="status"
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

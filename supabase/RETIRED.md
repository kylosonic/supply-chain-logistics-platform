# Supabase directory — RETIRED (NB-67)

**Status: retired history. Do not wire this back into the product.**

This directory is a leftover from an earlier plan to use Supabase for
authentication and as the hosted Postgres. The shipped product does **not** use
it:

- The platform's own FastAPI service owns identity end-to-end — company signup,
  login, JWT issuance (HttpOnly `SameSite=strict` cookie), roles, and
  organization memberships all live in `apps/platform-api/app/api/endpoints/auth.py`.
- No client imports `@supabase/supabase-js` any more (the dependency was removed
  from `apps/product-web` under NB-78).
- The frontend talks only to the platform API (`NEXT_PUBLIC_PLATFORM_API_URL`,
  `VITE_API_BASE_URL`).

## Why it was retired rather than hardened (NB-67)

The 2026-08-10 security audit (`docs/security-audit-2026-08-10.md`, finding
H-6) recorded this configuration as a landmine: if the Supabase project were
ever connected to a signup flow again, it would ship with

- email confirmations **disabled** (`enable_confirmations = false`) — anyone
  could register with a victim's address,
- minimum password length 6 with no complexity requirement,
- `secure_password_change = false` — password change without re-authentication,
- no CAPTCHA,

so the auth path was hardened-or-retired per
`docs/behaviors/production-security-hardening.md` §7. It was **retired**.

## What is still intentionally kept

- `migrations/20260727153410_company_onboarding_and_profiles.sql` — the
  `public.company_profiles` table plus its `auth.uid()`-scoped RLS policies.
  This is applied history on a database that also serves as the platform's
  Postgres. It is not used by the application.
- `config.toml` — kept only so the Supabase CLI can still talk to the linked
  project for database operations (migrations/backups). Every `[auth]` setting
  in it is legacy and unused.

## Re-arming this path requires (all of them, first)

1. `enable_confirmations = true`
2. `minimum_password_length = 8` plus `lower_upper_letters_digits`
3. `secure_password_change = true`
4. CAPTCHA (Turnstile/hCaptcha) enabled
5. Remote dashboard review: rate limits, SMTP sender, session timebox
6. TOTP MFA available for console roles

Until all six are done, no signup flow may point at Supabase.

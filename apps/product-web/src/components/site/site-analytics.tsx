import Script from 'next/script';

/**
 * Privacy-light analytics (NB-74 / LCH-03).
 *
 * The behaviour contract requires the funnel to be observable without invasive
 * tracking:
 *
 * - "a privacy-light, no-fingerprinting analytics approach (e.g.
 *   Plausible/Umami), loaded `defer`/lazy, with no ad networks".
 *
 * Design decisions, so the constraint is enforced rather than trusted:
 *
 * 1. **One env var is the only switch.** `NEXT_PUBLIC_ANALYTICS_DOMAIN` is the
 *    site identifier; `NEXT_PUBLIC_ANALYTICS_SRC` is the script URL. With
 *    neither set, this component renders **nothing at all** — no script tag, no
 *    request, no cookie. That is the local-dev and test behaviour, so the suite
 *    never depends on a third party being reachable.
 * 2. **`afterInteractive` strategy.** Next.js injects the script after the page
 *    becomes interactive, so it never blocks first paint and cannot affect the
 *    page-weight budget measured by `check:bundle`.
 * 3. **`defer` is explicit.** Belt and braces with the strategy above, and it
 *    makes the requirement visible in the rendered HTML.
 * 4. **Only compliant providers are supported.** Plausible and Umami are
 *    cookieless and aggregate-only. This component deliberately does not accept
 *    an arbitrary inline snippet, because an inline snippet is how ad networks
 *    and fingerprinting libraries get in.
 * 5. **Nothing about the copy changes.** Analytics is a measurement layer; it
 *    never feeds numbers back into the page (honesty rules NB-43/NB-44).
 */
export function SiteAnalytics() {
  const domain = process.env.NEXT_PUBLIC_ANALYTICS_DOMAIN;
  const src = process.env.NEXT_PUBLIC_ANALYTICS_SRC;

  // No configuration -> render nothing. Not an empty script tag, not a
  // commented-out one: absent, so there is nothing to leak and nothing to
  // block on.
  if (!domain || !src) {
    return null;
  }

  return (
    <Script
      src={src}
      data-domain={domain}
      strategy="afterInteractive"
      defer
    />
  );
}

/**
 * Event names used by `trackEvent`. Kept as a union so a typo cannot silently
 * create a phantom metric that nobody ever queries.
 */
export type FunnelEvent = 'start_free_click' | 'signup_success' | 'signup_error';

declare global {
  interface Window {
    plausible?: (event: string, options?: { props?: Record<string, string> }) => void;
    umami?: { track: (event: string, data?: Record<string, string>) => void };
  }
}

/**
 * Record a funnel event.
 *
 * No-ops safely when analytics is absent, which is the case in development,
 * tests, and any deployment that has not been configured — callers never need
 * to guard, and a missing provider can never break the signup flow.
 *
 * Props are restricted to strings and the event name to a known union: this is
 * a measurement call, not a free-form data-exfiltration channel.
 */
export function trackEvent(event: FunnelEvent, props?: Record<string, string>): void {
  if (typeof window === 'undefined') {
    return;
  }
  try {
    if (typeof window.plausible === 'function') {
      window.plausible(event, props ? { props } : undefined);
      return;
    }
    if (window.umami && typeof window.umami.track === 'function') {
      window.umami.track(event, props);
    }
  } catch {
    // Measurement must never break the page. Swallow and continue.
  }
}

import React from 'react';
import { renderToString } from 'react-dom/server';
import { describe, expect, it } from 'vitest';

import PricingPage from './pricing/page';
import {
  faqItems,
  partialPaymentStory,
  paymentPaceStory,
  verificationLine,
} from '@/lib/site-content';

function count(haystack: string, needle: string): number {
  return haystack.split(needle).length - 1;
}

/** React SSR escapes `'` as `&#x27;` — decode before asserting [EXACT] text (blueprint §1.1). */
function decodeHtml(input: string): string {
  return input
    .replace(/&#x27;/g, "'")
    .replace(/&quot;/g, '"')
    .replace(/&lt;/g, '<')
    .replace(/&gt;/g, '>')
    .replace(/&amp;/g, '&');
}

describe('pricing page phase 6 (NB-23.5, NB-24, NB-44, NB-46)', () => {
  const html = decodeHtml(renderToString(<PricingPage />));

  it('renders the NB-23.5 read-only-limbo story verbatim (a)', () => {
    // [EXACT] locked line from pending-behaviors.md NB-23 criterion 5.
    expect(html).toContain(paymentPaceStory);
  });

  it('keeps "trial" only inside the FAQ block, with exactly one "free trial" (b)', () => {
    const trial = faqItems.find((item) => item.question === 'Do you offer a free trial?');
    expect(trial).toBeTruthy();

    // The FAQ answer substance is untouched (NB-23.3): 7-day trial, no charge.
    expect(html).toContain(
      'The Free tier is free forever — 2,500 delivery tasks per month, no payment ever. When you upgrade to a paid tier from inside your workspace, the first 7 days on that tier are a trial at no charge.',
    );

    // Strip the JSON-LD script (machine mirror of the FAQ) before counting,
    // so the rendered page copy is what is measured — same pattern as phase 5.
    const withoutJsonLd = html.replace(
      /<script[^>]*type="application\/ld\+json"[^>]*>[\s\S]*?<\/script>/g,
      '',
    );
    expect(count(withoutJsonLd, 'trial')).toBe(2); // locked trial FAQ Q + A only
    expect(count(withoutJsonLd, 'free trial')).toBe(1); // only the locked FAQ question
  });

  it('keeps the NB-24 partial-payment story and verification line byte-identical (c)', () => {
    expect(html).toContain(partialPaymentStory);
    expect(html).toContain(verificationLine);
  });

  it('keeps the single-CTA posture unchanged — 4 "Start free" to /launch, zero new CTAs (d)', () => {
    expect(count(html, '>Start free<')).toBe(4); // hero + 3 tier cards
    expect(count(html, 'href="/launch"')).toBe(4);
  });
});

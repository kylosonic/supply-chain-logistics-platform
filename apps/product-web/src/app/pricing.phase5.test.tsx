import React from 'react';
import { renderToString } from 'react-dom/server';
import { describe, expect, it } from 'vitest';

import PricingPage from './pricing/page';
import {
  faqItems,
  partialPaymentStory,
  pricingTiers,
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

describe('pricing page phase 5 (NB-46.4, NB-39, NB-44.3)', () => {
  const html = decodeHtml(renderToString(<PricingPage />));

  it('shows the locked ETB tier ladder with quotas and overage rates from TIER_SPECS', () => {
    expect(html).toContain('Starter');
    expect(html).toContain('4,500 ETB');
    expect(html).toContain('per month');
    expect(html).toContain('2,500 delivery tasks');
    expect(html).toContain('50 route optimizations');
    expect(html).toContain('0.20 ETB');
    expect(html).toContain('1.50 ETB');

    expect(html).toContain('Scale');
    expect(html).toContain('10,000 ETB');
    expect(html).toContain('per quarter');
    expect(html).toContain('5,000 delivery tasks');
    expect(html).toContain('250 route optimizations');
    expect(html).toContain('0.16 ETB');
    expect(html).toContain('1.00 ETB');

    expect(html).toContain('Enterprise');
    expect(html).toContain('45,000 ETB');
    expect(html).toContain('per quarter');
  });

  it('Enterprise shows its price — no "Contact sales" anywhere', () => {
    expect(html).not.toContain('Contact sales');
    expect(html).not.toContain('Talk to sales');
  });

  it('every CTA on the page reads "Start free" and goes to /launch', () => {
    expect(count(html, '>Start free<')).toBe(4); // hero + 3 tier cards
    expect(count(html, 'href="/launch"')).toBe(4);
    expect(html).not.toContain('Choose Starter');
    expect(html).not.toContain('Choose Scale');
  });

  it('has no "Most Popular" badge and no testimonials section', () => {
    expect(html).not.toContain('Most Popular');
    expect(html).not.toContain('Recommended');
    expect(html).not.toContain('What operators are saying');
    expect(html).not.toContain('Amina');
    expect(html).not.toContain('Northstar');
  });

  it('carries the partial-payment story verbatim and the verification line', () => {
    expect(html).toContain(partialPaymentStory);
    expect(html).toContain(verificationLine);
  });

  it('contains the exact trial Q/A, and "trial" appears nowhere else (NB-44.3)', () => {
    const trial = faqItems.find((item) => item.question === 'Do you offer a free trial?');
    expect(trial).toBeTruthy();
    expect(html).toContain('Do you offer a free trial?');
    expect(html).toContain(
      'The Free tier is free forever — 2,500 delivery tasks per month, no payment ever. When you upgrade to a paid tier from inside your workspace, the first 7 days on that tier are a trial at no charge.',
    );

    // Both "trial" occurrences live inside the rendered FAQ; nowhere else.
    // (The JSON-LD script is a machine mirror of the same FAQ — strip it
    // before counting, so the rendered page copy is what is measured.)
    const withoutJsonLd = html.replace(
      /<script[^>]*type="application\/ld\+json"[^>]*>[\s\S]*?<\/script>/g,
      '',
    );
    expect(count(withoutJsonLd, 'trial')).toBe(2);

    // The FAQ JSON-LD must still mirror the trial Q/A for SEO.
    expect(html).toContain('"name":"Do you offer a free trial?"');
  });

  it('ships tier + payment FAQs with the exact locked numbers', () => {
    expect(html).toContain('What does the Starter tier include?');
    expect(html).toContain('What does the Scale tier include?');
    expect(html).toContain('What does the Enterprise tier include?');
    expect(html).toContain('How do payments work?');
    expect(html).toContain('1,000 ETB');
  });
});

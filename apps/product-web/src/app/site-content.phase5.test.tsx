import { describe, expect, it } from 'vitest';

import {
  faqItems,
  footerNavigation,
  freeLine,
  howItWorksSteps,
  partialPaymentStory,
  pricingTiers,
  trustStripLine,
} from '@/lib/site-content';

describe('site-content phase 5 (NB-43, NB-39)', () => {
  it('fabricated exports are removed (testimonials, homeStats, premiumBadges, benefitStrip)', async () => {
    const mod = (await import('@/lib/site-content')) as Record<string, unknown>;

    expect('testimonials' in mod).toBe(false);
    expect('homeStats' in mod).toBe(false);
    expect('premiumBadges' in mod).toBe(false);
    expect('benefitStrip' in mod).toBe(false);
    expect('flagshipFeatures' in mod).toBe(false);
    expect('secondaryFeatures' in mod).toBe(false);
  });

  it('pricingTiers match the locked ETB ladder (TIER_SPECS)', () => {
    expect(pricingTiers).toEqual([
      {
        name: 'Starter',
        price_etb: 4500,
        billing_cycle: 'per month',
        included_units: { delivery_tasks: 2500, route_optimizations: 50 },
        overage_rates: { delivery_tasks: 0.2, route_optimizations: 1.5 },
        summary: 'First lift off Free tier',
      },
      {
        name: 'Scale',
        price_etb: 10000,
        billing_cycle: 'per quarter',
        included_units: { delivery_tasks: 5000, route_optimizations: 250 },
        overage_rates: { delivery_tasks: 0.16, route_optimizations: 1.0 },
        summary: 'Mid-size dispatch shop',
      },
      {
        name: 'Enterprise',
        price_etb: 45000,
        billing_cycle: 'per quarter',
        included_units: { delivery_tasks: null, route_optimizations: null },
        overage_rates: { delivery_tasks: null, route_optimizations: null },
        summary: 'Unlimited usage, dedicated support',
      },
    ]);
  });

  it('faqItems contain the locked trial FAQ', () => {
    const trial = faqItems.find((item) => item.question === 'Do you offer a free trial?');
    expect(trial?.answer).toBe(
      'The Free tier is free forever — 2,500 delivery tasks per month, no payment ever. When you upgrade to a paid tier from inside your workspace, the first 7 days on that tier are a trial at no charge.',
    );
  });

  it('locked copy exports are byte-exact', () => {
    expect(freeLine).toBe('Free forever — 2,500 delivery tasks / month, no payment ever. Start here.');
    expect(partialPaymentStory).toBe(
      'Partial payments welcome. Pay what your cash flow allows — send the receipt for each transfer, and your workspace unlocks when the full balance clears. If you overpay within 1,000 ETB, the surplus applies as credit to your next invoice.',
    );
    expect(trustStripLine).toBe(
      'Bank transfer to CBE or Dashen. No card required. Partial payments welcome. No hidden fees, no annual lock-in.',
    );
    expect(howItWorksSteps).toHaveLength(3);
  });

  it('footerNavigation contains no dead links', () => {
    const allLinks = Object.values(footerNavigation).flat();

    expect(allLinks.length).toBeGreaterThan(0);

    for (const link of allLinks) {
      expect(link.href).not.toBe('#');
      expect(link.href.startsWith('#')).toBe(false);
      expect(link.href).not.toBe('/privacy');
      expect(link.href).not.toBe('/terms');
      expect(link.href).not.toBe('/security');
      expect(link.href).not.toBe('/about');
      expect(link.href).not.toBe('/blog');
      expect(link.href).not.toBe('/careers');
      expect(link.href).not.toBe('/community');
    }
  });
});

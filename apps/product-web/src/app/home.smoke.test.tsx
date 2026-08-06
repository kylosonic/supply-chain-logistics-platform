import React from 'react';
import { renderToString } from 'react-dom/server';
import { describe, expect, it } from 'vitest';

import HomePage from './page';
import ContactPage from './contact/page';
import LaunchPage from './launch/page';
import PlatformPage from './platform/page';
import PricingPage from './pricing/page';
import TechnologyPage from './technology/page';
import { heroHeadline, heroParagraph } from '@/lib/site-content';

/** React SSR escapes `'` as `&#x27;` — decode before asserting [EXACT] text (blueprint §1.1). */
function decodeHtml(input: string): string {
  return input
    .replace(/&#x27;/g, "'")
    .replace(/&quot;/g, '"')
    .replace(/&lt;/g, '<')
    .replace(/&gt;/g, '>')
    .replace(/&amp;/g, '&');
}

describe('product-web next home smoke (phase 5 locked copy)', () => {
  it('renders the locked hero headline and paragraph', () => {
    const html = decodeHtml(renderToString(<HomePage />));

    expect(html).toContain(heroHeadline);
    expect(html).toContain(heroParagraph);
    expect(html).toContain('data-section="hero"');
    expect(html).toContain('data-section="how-it-works"');
    expect(html).toContain('data-section="pricing-summary"');
    expect(html).toContain('data-section="trust-strip"');
    expect(html).toContain('data-section="final-cta"');
  });
});

describe('product-web page smoke tests', () => {
  it('renders the platform page', () => {
    const html = renderToString(<PlatformPage />);
    expect(html).toContain('FreightPilot');
    expect(html.length).toBeGreaterThan(500);
    expect(html.length).toBeLessThan(120_000);
  });

  it('renders the technology page', () => {
    const html = renderToString(<TechnologyPage />);
    expect(html).toContain('FreightPilot');
    expect(html.length).toBeGreaterThan(500);
    expect(html.length).toBeLessThan(120_000);
  });

  it('renders the pricing page', () => {
    const html = renderToString(<PricingPage />);
    expect(html).toContain('4,500 ETB');
    expect(html).toContain('Do you offer a free trial?');
    expect(html.length).toBeGreaterThan(500);
    expect(html.length).toBeLessThan(160_000);
  });

  it('renders the launch page', () => {
    const html = renderToString(<LaunchPage />);
    expect(html).toContain('Start free, no card required.');
    expect(html.length).toBeGreaterThan(500);
    expect(html.length).toBeLessThan(120_000);
  });

  it('renders the contact page', () => {
    const html = renderToString(<ContactPage />);
    expect(html).toContain('Send a message');
    expect(html.length).toBeGreaterThan(500);
    expect(html.length).toBeLessThan(80_000);
  });
});

import React from 'react';
import { renderToString } from 'react-dom/server';
import { describe, expect, it } from 'vitest';

import HomePage from './page';
import {
  freeLine,
  heroHeadline,
  heroParagraph,
  howItWorksHeading,
  howItWorksSteps,
  partialPaymentStory,
  showLabel,
  trustStripLine,
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

/** Extract the HTML of a single top-level section by its data-section name. */
function sectionHtml(html: string, name: string): string {
  const marker = `data-section="${name}"`;
  const markerIndex = html.indexOf(marker);
  expect(markerIndex).toBeGreaterThan(-1);
  const sectionStart = html.lastIndexOf('<section', markerIndex);
  const sectionEnd = html.indexOf('</section>', markerIndex);
  return html.slice(sectionStart, sectionEnd + '</section>'.length);
}

describe('home page phase 5 (NB-36..44 locked copy)', () => {
  it('renders the locked hero headline and paragraph byte-exact', () => {
    const html = decodeHtml(renderToString(<HomePage />));
    expect(html).toContain(heroHeadline);
    expect(html).toContain(heroParagraph);
  });

  it('hero contains exactly one "Start free" CTA to /launch and no competing CTAs', () => {
    const html = renderToString(<HomePage />);
    const hero = sectionHtml(html, 'hero');

    expect(count(hero, 'href="/launch"')).toBe(1);
    expect(count(hero, '>Start free<')).toBe(1);

    for (const forbidden of [
      'Start free trial',
      'Try FreightPilot',
      'Get started',
      'See pricing',
      'Book a demo',
      'Download desktop',
      'Limited spots',
      'Offer ends',
      'Act now',
      'Hurry',
    ]) {
      expect(hero).not.toContain(forbidden);
    }
  });

  it('has exactly five sections in locked order hero → how-it-works → pricing-summary → trust-strip → final-cta', () => {
    const html = renderToString(<HomePage />);
    const order = ['hero', 'how-it-works', 'pricing-summary', 'trust-strip', 'final-cta'];
    let pos = -1;
    for (const name of order) {
      const idx = html.indexOf(`data-section="${name}"`);
      expect(idx).toBeGreaterThan(pos);
      pos = idx;
    }
    expect(count(html, 'data-section="')).toBe(5);
  });

  it('contains no fabricated social proof, logos, or compare markers', () => {
    const html = renderToString(<HomePage />);
    for (const marker of [
      'What operators are saying',
      'Amina',
      'Northstar',
      'Contour',
      'Helix',
      'Trusted by',
      'testimonial',
      ' vs ',
    ]) {
      expect(html).not.toContain(marker);
    }
  });

  it('how-it-works renders heading + Show affordance, steps hidden in initial HTML, text + icons only', () => {
    const html = renderToString(<HomePage />);
    const section = sectionHtml(html, 'how-it-works');

    expect(html).toContain(howItWorksHeading);
    expect(html).toContain(showLabel);
    expect(section).not.toContain('<img');
    expect(section).not.toContain('<video');

    // Locked three-step array: exact strings, in order, no fourth step.
    expect(howItWorksSteps).toEqual([
      'Sign up free — your workspace loads with sample data in under a minute.',
      'Run your first route optimization on the sample data — see the map, the stops, the schedule.',
      'Upload your real CSVs (warehouses, items, fleet, inventory, orders) when you\'re ready. Pay by bank transfer to CBE or Dashen when you outgrow the free tier.',
    ]);

    // Collapsed by default: no step text in the initial SSR HTML.
    for (const step of howItWorksSteps) {
      expect(html).not.toContain(step);
    }
  });

  it('pricing summary renders the locked rows, Free line, and partial-payment story verbatim', () => {
    const html = renderToString(<HomePage />);

    expect(html).toContain('Starter');
    expect(html).toContain('4,500 ETB');
    expect(html).toContain('per month');
    expect(html).toContain('First lift off Free tier');
    expect(html).toContain('Scale');
    expect(html).toContain('10,000 ETB');
    expect(html).toContain('per quarter');
    expect(html).toContain('Mid-size dispatch shop');
    expect(html).toContain('Enterprise');
    expect(html).toContain('45,000 ETB');
    expect(html).toContain('Unlimited usage, dedicated support');

    expect(html).toContain(freeLine);
    expect(html).toContain(partialPaymentStory);

    expect(html).not.toContain('Most Popular');
    expect(html).not.toContain('Recommended');
    expect(html).not.toContain('Contact sales');
  });

  it('trust strip renders the locked line verbatim with zero links', () => {
    const html = renderToString(<HomePage />);
    expect(html).toContain(trustStripLine);

    const trust = sectionHtml(html, 'trust-strip');
    expect(trust).not.toContain('<a ');
    expect(trust).not.toContain('href=');
  });

  it('final CTA section holds exactly one "Start free" CTA with no companions', () => {
    const html = renderToString(<HomePage />);
    const final = sectionHtml(html, 'final-cta');

    expect(count(final, 'href="/launch"')).toBe(1);
    expect(count(final, '>Start free<')).toBe(1);
    expect(count(final, '>Start free<')).toBe(count(final, 'href="/launch"'));
  });

  it('home SSR uses exactly one framer entrance and zero whileInView markers (NB-42.5)', () => {
    const html = renderToString(<HomePage />);

    const initialStates = html.match(/style="[^"]*opacity:0/g) || [];
    expect(initialStates).toHaveLength(1);

    expect(html).toContain('data-hero-entrance');
    expect(html).not.toContain('whileInView');
  });

  it('contains no "free trial"/"trial" language (NB-44)', () => {
    const html = renderToString(<HomePage />);
    expect(html).not.toContain('free trial');
    expect(html).not.toContain('trial');
  });

  it('stays under the 120 KB SSR HTML cap (NB-42.1 regression net)', () => {
    const html = renderToString(<HomePage />);
    expect(html.length).toBeLessThan(120_000);
  });
});

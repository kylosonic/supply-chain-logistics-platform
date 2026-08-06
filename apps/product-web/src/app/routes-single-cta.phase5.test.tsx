import React from 'react';
import { renderToString } from 'react-dom/server';
import { describe, expect, it, vi } from 'vitest';

import LaunchPage from './launch/page';
import PlatformPage from './platform/page';
import PricingPage from './pricing/page';
import TechnologyPage from './technology/page';

vi.mock('next/navigation', () => ({
  usePathname: () => '/',
}));

import { SiteChrome } from '@/components/site/site-chrome';

const PRIMARY_CLASS = 'bg-gradient-to-r from-sky-400 via-cyan-300 to-violet-300';

function count(haystack: string, needle: string): number {
  return haystack.split(needle).length - 1;
}

describe('single-CTA rule across routes (NB-46.3)', () => {
  it('platform page: exactly one primary CTA reading "Start free" → /launch, no secondary hero actions', () => {
    const html = renderToString(<PlatformPage />);

    expect(count(html, PRIMARY_CLASS)).toBe(1);
    expect(count(html, '>Start free<')).toBe(1);
    expect(count(html, 'href="/launch"')).toBe(1);

    expect(html).not.toContain('Open control tower');
    expect(html).not.toContain('Review docs');
    expect(html).not.toContain('Launch the workspace');
  });

  it('technology page: exactly one primary CTA reading "Start free" → /launch, no secondary hero actions', () => {
    const html = renderToString(<TechnologyPage />);

    expect(count(html, PRIMARY_CLASS)).toBe(1);
    expect(count(html, '>Start free<')).toBe(1);
    expect(count(html, 'href="/launch"')).toBe(1);

    expect(html).not.toContain('Review docs');
    expect(html).not.toContain('Explore pricing');
  });

  it('pricing page: one primary CTA; every CTA reads "Start free" → /launch', () => {
    const html = renderToString(<PricingPage />);

    expect(count(html, PRIMARY_CLASS)).toBe(1); // hero CTA only; card CTAs are secondary-styled
    expect(count(html, '>Start free<')).toBe(4);
    expect(count(html, 'href="/launch"')).toBe(4);
  });

  it('launch page: the form submit button is the single primary CTA; no hero secondary actions', () => {
    const html = renderToString(<LaunchPage />);

    expect(count(html, PRIMARY_CLASS)).toBe(1);
    expect(html).toContain('>Start free<');
    expect(html).not.toContain('Get desktop');
    expect(html).not.toContain('Review docs');
  });
});

describe('site chrome (NB-46.3)', () => {
  it('nav CTA reads "Start free" → /launch and is the only primary-styled element', () => {
    const html = renderToString(
      <SiteChrome>
        <div />
      </SiteChrome>,
    );

    expect(count(html, PRIMARY_CLASS)).toBe(1);
    expect(html).toContain('>Start free<');
    expect(html).toContain('href="/launch"');
  });

  it('footer has no primary-styled buttons and exposes a plain Contact text link', () => {
    const html = renderToString(
      <SiteChrome>
        <div />
      </SiteChrome>,
    );

    const footerStart = html.indexOf('<footer');
    const footer = html.slice(footerStart);
    expect(footer).not.toContain(PRIMARY_CLASS);
    expect(footer).not.toContain('Contact Sales');
    expect(footer).toContain('>Contact<');
    expect(footer).toContain('href="/contact"');
  });

  it('footer contains no dead links (# or non-existent routes)', () => {
    const html = renderToString(
      <SiteChrome>
        <div />
      </SiteChrome>,
    );

    expect(html).not.toContain('href="#"');
    expect(html).not.toContain('href="/privacy"');
    expect(html).not.toContain('href="/terms"');
    expect(html).not.toContain('href="/security"');
    expect(html).not.toContain('>About<');
    expect(html).not.toContain('>Blog<');
    expect(html).not.toContain('>Careers<');
    expect(html).not.toContain('>Community<');
  });
});

import React from 'react';
import { renderToString } from 'react-dom/server';
import { describe, expect, it } from 'vitest';

import HomePage from './page';
import ContactPage from './contact/page';
import LaunchPage from './launch/page';
import PlatformPage from './platform/page';
import PricingPage from './pricing/page';
import TechnologyPage from './technology/page';

describe('product-web next home smoke', () => {
  it('renders the hero narrative and launch CTA', () => {
    const html = renderToString(<HomePage />);

    expect(html).toContain('Plan routes, manage exceptions, and launch operations from one control layer.');
    expect(html).toContain('Launch your workspace');
    expect(html).toContain('Explore the platform');
  });
});

describe('product-web page smoke tests', () => {
  it('renders the platform page', () => {
    const html = renderToString(<PlatformPage />);
    expect(html).toContain('FreightPilot');
    expect(html.length).toBeGreaterThan(500);
  });

  it('renders the technology page', () => {
    const html = renderToString(<TechnologyPage />);
    expect(html).toContain('FreightPilot');
    expect(html.length).toBeGreaterThan(500);
  });

  it('renders the pricing page', () => {
    const html = renderToString(<PricingPage />);
    expect(html).toContain('FreightPilot');
    expect(html.length).toBeGreaterThan(500);
  });

  it('renders the launch page', () => {
    const html = renderToString(<LaunchPage />);
    expect(html).toContain('Set up the workspace and launch operations in stages');
    expect(html.length).toBeGreaterThan(500);
  });

  it('renders the contact page', () => {
    const html = renderToString(<ContactPage />);
    expect(html).toContain('Send a message');
    expect(html.length).toBeGreaterThan(500);
  });
});

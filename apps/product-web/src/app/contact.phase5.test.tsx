import React from 'react';
import { renderToString } from 'react-dom/server';
import { describe, expect, it } from 'vitest';

import ContactPage from './contact/page';

describe('contact page phase 5 (NB-46.6, NB-43)', () => {
  const html = renderToString(<ContactPage />);

  it('contains no fabricated contact details', () => {
    expect(html).not.toContain('555-0199');
    expect(html).not.toContain('San Francisco');
    expect(html).not.toContain('100 Logistics Way');
    expect(html).not.toContain('Suite 400');
  });

  it('makes no numeric reply-time promise', () => {
    expect(html).not.toContain('24 hours');
    expect(html).not.toContain('within 24');
  });

  it('uses honest manual-reply copy', () => {
    expect(html).toContain('We read every message. Replies are manual and may take a few days.');
  });

  it('still renders the email card and the message form', () => {
    expect(html).toContain('nahomgwmichael@gmail.com');
    expect(html).toContain('Send a message');
  });

  it('has no CTA buttons and no drip/CRM language', () => {
    expect(html).not.toContain('Start free');
    expect(html).not.toContain('href="/launch"');
    expect(html).not.toContain('bg-gradient-to-r from-sky-400');
    expect(html).not.toContain('sales team');
    expect(html).not.toContain('drip');
    expect(html).not.toContain('CRM');
  });
});

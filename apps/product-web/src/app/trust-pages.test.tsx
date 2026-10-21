import { renderToString } from 'react-dom/server';
import { describe, expect, it } from 'vitest';

import PrivacyPage from './privacy/page';
import SecurityPage from './security/page';
import StatusPage from './status/page';
import TermsPage from './terms/page';

describe('public trust pages', () => {
  it('privacy page states the data boundary without claiming a certification', () => {
    const html = renderToString(<PrivacyPage />);

    expect(html).toContain('Data we process');
    expect(html).toContain('not a substitute for a signed customer data-processing agreement');
    expect(html).toContain('not sold or used to train a shared public model');
  });

  it('terms page keeps recommendations advisory', () => {
    const html = renderToString(<TermsPage />);

    expect(html).toContain('decision support');
    expect(html).toContain('An authorized operator remains responsible');
  });

  it('security page states current limits', () => {
    const html = renderToString(<SecurityPage />);

    expect(html).toContain('Controls in place');
    expect(html).toContain('not a claim of SOC 2');
    expect(html).toContain('Report a vulnerability');
  });

  it('status page limits its health claim to the API and database', () => {
    const html = renderToString(<StatusPage />);

    expect(html).toContain('What this page checks');
    expect(html).toContain('does not prove that every route');
    expect(html).toContain('CHECKING');
  });
});

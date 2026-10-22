import { renderToString } from 'react-dom/server';
import { StaticRouter } from 'react-router';
import { describe, expect, it } from 'vitest';

import { AcceptInvitePage } from './AcceptInvitePage';

describe('invitation acceptance surface', () => {
  it('fails closed when the fragment token is absent', () => {
    const html = renderToString(
      <StaticRouter location="/accept-invite">
        <AcceptInvitePage />
      </StaticRouter>,
    );

    expect(html).toContain('Accept your invitation');
    expect(html).toContain('This invitation link is missing a token.');
  });
});

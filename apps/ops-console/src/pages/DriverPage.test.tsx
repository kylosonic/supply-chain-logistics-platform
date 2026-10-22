import { renderToString } from 'react-dom/server';
import { StaticRouter } from 'react-router';
import { describe, expect, it } from 'vitest';

import { DriverPage } from './DriverPage';

describe('driver surface', () => {
  it('defaults to Amharic and renders the phone-first manifest shell', () => {
    const html = renderToString(
      <StaticRouter location="/driver">
        <DriverPage />
      </StaticRouter>,
    );

    expect(html).toContain('የዛሬ ጉዞ');
    expect(html).toContain('FreightPilot Driver');
    expect(html).toContain('>EN<');
  });
});

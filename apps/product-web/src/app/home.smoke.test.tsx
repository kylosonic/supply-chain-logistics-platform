import React from 'react';
import { renderToString } from 'react-dom/server';
import { describe, expect, it } from 'vitest';

import HomePage from './page';

describe('product-web next home smoke', () => {
  it('renders the new premium hero narrative and launch CTA', () => {
    const html = renderToString(<HomePage />);

    expect(html).toContain('The logistics command layer for teams who want the future to feel real.');
    expect(html).toContain('Create company workspace');
    expect(html).toContain('FreightPilot 2026 launch');
  });
});
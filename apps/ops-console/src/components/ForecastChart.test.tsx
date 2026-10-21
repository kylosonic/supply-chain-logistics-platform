import { renderToString } from 'react-dom/server';
import { describe, expect, it } from 'vitest';

import { ForecastChart } from './ForecastChart';
import type { ForecastQuality } from '../types/api';

function quality(overrides: Partial<ForecastQuality> = {}): ForecastQuality {
  return {
    status: 'validated',
    history_weeks: 10,
    holdout_weeks: 2,
    evaluated_rows: 8,
    mae: 4.2,
    wape_percent: 18.5,
    range_basis: 'ensemble_p10_p90_widened_by_holdout_error',
    interpretation: 'Held-out error is within 20% of actual demand.',
    caveat: 'This is not a guarantee of future demand.',
    ...overrides,
  };
}

function render(dataQuality: ForecastQuality): string {
  return renderToString(<ForecastChart points={[]} quality={dataQuality} modelName="RandomForestRegressor" />)
    .replace(/<!-- -->/g, '');
}

describe('ForecastChart evidence labels', () => {
  it('states when the range is widened by measured holdout error', () => {
    const html = render(quality());

    expect(html).toContain('RandomForestRegressor');
    expect(html).toContain('18.5% WAPE');
    expect(html).toContain('Planning range widens ensemble spread by held-out error');
  });

  it('refuses to claim a holdout-widened range when history is insufficient', () => {
    const html = render(
      quality({
        status: 'insufficient_history',
        history_weeks: 2,
        holdout_weeks: 0,
        evaluated_rows: 0,
        mae: null,
        wape_percent: null,
        range_basis: 'ensemble_p10_p90',
        caveat: 'No held-out backtest can be reported.',
      }),
    );

    expect(html).toContain('Not available');
    expect(html).toContain('ensemble spread only');
    expect(html).not.toContain('Planning range widens ensemble spread by held-out error');
  });

  it('does not render high-error validation as an unqualified success', () => {
    const html = render(quality({ wape_percent: 48.2 }));

    expect(html).toContain('validated - high error');
    expect(html).not.toContain('>Validated<');
  });
});

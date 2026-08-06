// @vitest-environment jsdom
import React from 'react';
import { cleanup, render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, describe, expect, it } from 'vitest';

import { HowItWorks } from '@/components/site/how-it-works';
import { hideLabel, howItWorksHeading, howItWorksSteps, showLabel } from '@/lib/site-content';

afterEach(cleanup);

describe('how-it-works (NB-38)', () => {
  it('is collapsed by default: heading + Show affordance only, steps not in document', () => {
    render(<HowItWorks />);

    expect(screen.getByText(howItWorksHeading)).toBeTruthy();
    expect(screen.getByRole('button', { name: showLabel })).toBeTruthy();

    for (const step of howItWorksSteps) {
      expect(screen.queryByText(step)).toBeNull();
    }
    expect(screen.queryAllByRole('listitem')).toHaveLength(0);
  });

  it('expands on Show with exactly three steps in locked order', async () => {
    const user = userEvent.setup();
    render(<HowItWorks />);

    await user.click(screen.getByRole('button', { name: showLabel }));

    const items = screen.getAllByRole('listitem');
    expect(items).toHaveLength(3);
    for (let i = 0; i < howItWorksSteps.length; i++) {
      expect(items[i].textContent).toContain(howItWorksSteps[i]);
    }
    expect(screen.getByRole('button', { name: hideLabel })).toBeTruthy();
  });

  it('collapses back via the same affordance (NB-38.5)', async () => {
    const user = userEvent.setup();
    render(<HowItWorks />);

    await user.click(screen.getByRole('button', { name: showLabel }));
    expect(screen.getAllByRole('listitem')).toHaveLength(3);

    await user.click(screen.getByRole('button', { name: hideLabel }));

    for (const step of howItWorksSteps) {
      expect(screen.queryByText(step)).toBeNull();
    }
    expect(screen.getByRole('button', { name: showLabel })).toBeTruthy();
  });

  it('toggles aria-expanded on the control', async () => {
    const user = userEvent.setup();
    render(<HowItWorks />);

    const button = screen.getByRole('button', { name: showLabel });
    expect(button.getAttribute('aria-expanded')).toBe('false');

    await user.click(button);
    expect(button.getAttribute('aria-expanded')).toBe('true');

    await user.click(button);
    expect(button.getAttribute('aria-expanded')).toBe('false');
  });
});

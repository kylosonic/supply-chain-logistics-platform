// @vitest-environment jsdom
import React from 'react';
import { cleanup, render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { SignupForm } from '@/components/site/signup-form';
import {
  externalLinks,
  signupFormNote,
  signupFormSubline,
  signupSuccessMessage,
} from '@/lib/site-content';

const assignMock = vi.fn();

function mockLocationAssign() {
  Object.defineProperty(window, 'location', {
    value: { assign: assignMock },
    writable: true,
    configurable: true,
  });
}

function jsonResponse(body: unknown, ok: boolean) {
  return {
    ok,
    json: async () => body,
    text: async () => (typeof body === 'string' ? body : JSON.stringify(body)),
  };
}

async function fillRequiredFields(user: ReturnType<typeof userEvent.setup>) {
  // Sequential typing — user-event is not concurrency-safe.
  await user.type(screen.getByPlaceholderText('Company name'), 'Acme Logistics');
  await user.type(screen.getByPlaceholderText('Company email'), 'ops@acme.com');
  await user.type(screen.getByPlaceholderText('Password'), 'strong-pass-123');
}

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
});

beforeEach(() => {
  mockLocationAssign();
  assignMock.mockReset();
});

describe('launch signup form phase 5 (NB-46.5, NB-44.4, NB-25)', () => {
  it('renders "Start free, no card required." with no trial language', () => {
    render(<SignupForm />);

    expect(screen.getByText(signupFormSubline)).toBeTruthy();
    expect(screen.getByText(signupFormNote)).toBeTruthy();
    expect(screen.getByRole('button', { name: 'Start free' })).toBeTruthy();
    expect(screen.queryByText(/free trial/i)).toBeNull();
    expect(screen.queryByText(/trial/i)).toBeNull();
  });

  it('tier preference is optional with no preselection; unset tier is omitted from the payload', async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      jsonResponse({ user: { id: 'u-1', email: 'ops@acme.com' } }, true),
    );
    vi.stubGlobal('fetch', fetchMock);

    const user = userEvent.setup();
    render(<SignupForm />);

    const radios = screen.getAllByRole('radio') as HTMLInputElement[];
    expect(radios).toHaveLength(3);
    expect(radios.every((radio) => !radio.checked)).toBe(true);
    expect(screen.getByText(/Optional — choose a tier later inside your workspace/)).toBeTruthy();
    expect(screen.getByText('Starter — 4,500 ETB/month')).toBeTruthy();
    expect(screen.getByText('Scale — 10,000 ETB/quarter')).toBeTruthy();
    expect(screen.getByText('Enterprise — 45,000 ETB/quarter')).toBeTruthy();

    await fillRequiredFields(user);
    await user.click(screen.getByRole('button', { name: 'Start free' }));

    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(1));
    const [url, init] = fetchMock.mock.calls[0] as [string, { body: string }];
    expect(url).toContain('/auth/company-signup');

    const payload = JSON.parse(init.body);
    expect(payload.subscription_tier).toBeUndefined();
    expect(payload.company_email).toBe('ops@acme.com');
  });

  it('full name is optional and omitted from the payload when left empty', async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      jsonResponse({ user: { id: 'u-1', email: 'ops@acme.com' } }, true),
    );
    vi.stubGlobal('fetch', fetchMock);

    const user = userEvent.setup();
    render(<SignupForm />);

    await fillRequiredFields(user);
    await user.click(screen.getByRole('button', { name: 'Start free' }));

    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(1));
    const payload = JSON.parse((fetchMock.mock.calls[0][1] as { body: string }).body);
    expect(payload.full_name).toBeUndefined();
  });

  it('shows inline errors for an invalid email and short password', async () => {
    const user = userEvent.setup();
    render(<SignupForm />);

    await user.type(screen.getByPlaceholderText('Company name'), 'Acme Logistics');
    await user.type(screen.getByPlaceholderText('Company email'), 'not-an-email');
    await user.type(screen.getByPlaceholderText('Password'), 'short');
    await user.click(screen.getByRole('button', { name: 'Start free' }));

    expect(await screen.findByText('Use a valid company email.')).toBeTruthy();
    expect(screen.getByText('Use at least 8 characters.')).toBeTruthy();
  });

  it('surfaces a 400 public-email rejection verbatim from the FastAPI detail field', async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValue(jsonResponse({ detail: 'Please use your company email domain' }, false));
    vi.stubGlobal('fetch', fetchMock);

    const user = userEvent.setup();
    render(<SignupForm />);

    await fillRequiredFields(user);
    await user.click(screen.getByRole('button', { name: 'Start free' }));

    expect(await screen.findByText('Please use your company email domain')).toBeTruthy();
  });

  it('surfaces a 409 duplicate-account rejection verbatim', async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValue(jsonResponse({ detail: 'A user with this email already exists' }, false));
    vi.stubGlobal('fetch', fetchMock);

    const user = userEvent.setup();
    render(<SignupForm />);

    await fillRequiredFields(user);
    await user.click(screen.getByRole('button', { name: 'Start free' }));

    expect(await screen.findByText('A user with this email already exists')).toBeTruthy();
  });

  it('on 201 shows the locked success message and redirects to the console URL (NB-46.5)', async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      jsonResponse({ user: { id: 'u-1', email: 'ops@acme.com' } }, true),
    );
    vi.stubGlobal('fetch', fetchMock);

    const user = userEvent.setup();
    render(<SignupForm />);

    await fillRequiredFields(user);
    await user.click(screen.getByRole('button', { name: 'Start free' }));

    expect(await screen.findByText(signupSuccessMessage)).toBeTruthy();
    expect(assignMock).toHaveBeenCalledWith(externalLinks.console);
  });

  it('shows the honest network-failure fallback when fetch rejects', async () => {
    vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new TypeError('Failed to fetch')));

    const user = userEvent.setup();
    render(<SignupForm />);

    await fillRequiredFields(user);
    await user.click(screen.getByRole('button', { name: 'Start free' }));

    expect(
      await screen.findByText('Could not create the company workspace. Check your connection and try again.'),
    ).toBeTruthy();
  });
});

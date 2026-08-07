import { describe, expect, it } from 'vitest';

import {
  ADMIN_ALREADY_EXISTS_MESSAGE,
  apiDetail,
  bootstrapErrorMessage,
} from './authErrors';

describe('apiDetail', () => {
  it('extracts the FastAPI detail from an axios-shaped error', () => {
    const err = { response: { data: { detail: 'Admin authentication required' } } };
    expect(apiDetail(err)).toBe('Admin authentication required');
  });

  it('falls back to Error.message when no response shape', () => {
    expect(apiDetail(new Error('Network Error'))).toBe('Network Error');
  });

  it('returns null for unknown shapes', () => {
    expect(apiDetail('string')).toBeNull();
    expect(apiDetail(null)).toBeNull();
    expect(apiDetail(undefined)).toBeNull();
  });
});

describe('bootstrapErrorMessage', () => {
  it('maps the admin-exists 401 to actionable guidance', () => {
    const err = { response: { data: { detail: 'Admin authentication required' } } };
    expect(bootstrapErrorMessage(err, 'fallback')).toBe(ADMIN_ALREADY_EXISTS_MESSAGE);
  });

  it('passes through other API details', () => {
    const err = { response: { data: { detail: 'Username already exists' } } };
    expect(bootstrapErrorMessage(err, 'fallback')).toBe('Username already exists');
  });

  it('uses the fallback when nothing is extractable', () => {
    expect(bootstrapErrorMessage('junk', 'Failed to create initial admin')).toBe(
      'Failed to create initial admin',
    );
  });
});

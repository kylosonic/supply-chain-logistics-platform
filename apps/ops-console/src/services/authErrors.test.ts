import { describe, expect, it } from 'vitest';

import { apiDetail } from './authErrors';

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

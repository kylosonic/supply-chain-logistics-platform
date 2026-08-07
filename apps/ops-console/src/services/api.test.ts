import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { api, clearAuthStorage, getStoredToken, setStoredToken } from './api';

const sessionMock = (() => {
  let store: Record<string, string> = {};
  return {
    getItem: (k: string) => store[k] ?? null,
    setItem: (k: string, v: string) => { store[k] = String(v); },
    removeItem: (k: string) => { delete store[k]; },
    clear: () => { store = {}; },
  };
})();

const localMock = (() => {
  let store: Record<string, string> = {};
  return {
    getItem: (k: string) => store[k] ?? null,
    setItem: (k: string, v: string) => { store[k] = String(v); },
    removeItem: (k: string) => { delete store[k]; },
  };
})();

describe('token storage', () => {
  beforeEach(() => {
    vi.stubGlobal('sessionStorage', sessionMock);
    vi.stubGlobal('localStorage', localMock);
  });
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it('round-trips the token', () => {
    expect(getStoredToken()).toBeNull();
    setStoredToken('tok-123');
    expect(getStoredToken()).toBe('tok-123');
    setStoredToken(null);
    expect(getStoredToken()).toBeNull();
  });

  it('clearAuthStorage removes both token and org id', () => {
    setStoredToken('tok-123');
    localMock.setItem('supply_chain_org_id', 'org-9');
    clearAuthStorage();
    expect(getStoredToken()).toBeNull();
    expect(localMock.getItem('supply_chain_org_id')).toBeNull();
  });
});

describe('request interceptor', () => {
  let captured: { headers?: Record<string, unknown> } = {};

  beforeEach(() => {
    vi.stubGlobal('sessionStorage', sessionMock);
    vi.stubGlobal('localStorage', localMock);
    captured = {};
    api.defaults.adapter = async (config) => {
      captured = config;
      return { data: {}, status: 200, statusText: 'OK', headers: {}, config };
    };
  });
  afterEach(() => {
    vi.unstubAllGlobals();
    delete api.defaults.adapter;
  });

  it('attaches the bearer token when one is stored', async () => {
    setStoredToken('tok-456');
    await api.get('/auth/me');
    const auth = (captured.headers as Record<string, unknown>)?.Authorization;
    expect(auth).toBe('Bearer tok-456');
  });

  it('sends no Authorization header when no token is stored', async () => {
    setStoredToken(null);
    await api.get('/auth/me');
    const auth = (captured.headers as Record<string, unknown>)?.Authorization;
    expect(auth).toBeUndefined();
  });
});

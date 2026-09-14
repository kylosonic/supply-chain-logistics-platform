import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import {
  api,
  beginAuthSessionEstablishment,
  clearAuthStorage,
  endAuthSessionEstablishment,
  getStoredToken,
  onAuthSessionExpired,
  setStoredToken,
} from './api';

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
  const store: Record<string, string> = {};
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

describe('response interceptor — soft session reset (NB-59)', () => {
  let assigns: string[];

  beforeEach(() => {
    vi.stubGlobal('sessionStorage', sessionMock);
    vi.stubGlobal('localStorage', localMock);
    assigns = [];
    vi.stubGlobal('window', {
      location: {
        pathname: '/',
        assign: (url: string) => { assigns.push(url); },
      },
    });
  });
  afterEach(() => {
    vi.unstubAllGlobals();
    delete api.defaults.adapter;
  });

  /** Rejecting adapter that simulates a refused request. */
  function rejectWith401() {
    api.defaults.adapter = async () => {
      throw { response: { status: 401 } };
    };
  }

  it('clears auth storage and signals listeners on 401 with a stored token — no window redirect', async () => {
    setStoredToken('tok-401');
    localMock.setItem('supply_chain_org_id', 'org-1');
    const listener = vi.fn();
    const unsubscribe = onAuthSessionExpired(listener);
    rejectWith401();

    await expect(api.get('/data')).rejects.toMatchObject({ response: { status: 401 } });

    expect(getStoredToken()).toBeNull();
    expect(localMock.getItem('supply_chain_org_id')).toBeNull();
    expect(listener).toHaveBeenCalledTimes(1);
    expect(assigns).toEqual([]);
    unsubscribe();
  });

  it('retains the token and stays silent when a 401 lands while a session is being established', async () => {
    setStoredToken('tok-fresh');
    const listener = vi.fn();
    const unsubscribe = onAuthSessionExpired(listener);
    rejectWith401();

    beginAuthSessionEstablishment();
    try {
      await expect(api.get('/auth/me')).rejects.toMatchObject({ response: { status: 401 } });
    } finally {
      endAuthSessionEstablishment();
    }

    expect(getStoredToken()).toBe('tok-fresh');
    expect(listener).not.toHaveBeenCalled();
    expect(assigns).toEqual([]);
    unsubscribe();
  });

  it('leaves storage untouched and fires nothing on a 401 with no token and no org id (login failure)', async () => {
    setStoredToken(null);
    const listener = vi.fn();
    const unsubscribe = onAuthSessionExpired(listener);
    rejectWith401();

    await expect(api.post('/auth/login', {})).rejects.toMatchObject({ response: { status: 401 } });

    expect(getStoredToken()).toBeNull();
    expect(localMock.getItem('supply_chain_org_id')).toBeNull();
    expect(listener).not.toHaveBeenCalled();
    expect(assigns).toEqual([]);
    unsubscribe();
  });

  it('stops notifying a listener after it unsubscribes', async () => {
    setStoredToken('tok-401');
    const listener = vi.fn();
    const unsubscribe = onAuthSessionExpired(listener);
    unsubscribe();
    rejectWith401();

    await expect(api.get('/data')).rejects.toMatchObject({ response: { status: 401 } });

    expect(listener).not.toHaveBeenCalled();
  });
});

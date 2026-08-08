import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api/v1';

const ORG_ID_KEY = 'supply_chain_org_id';
const TOKEN_KEY = 'supply_chain_token';

export function getStoredOrgId(): string | null {
  return localStorage.getItem(ORG_ID_KEY);
}

export function setStoredOrgId(orgId: string | null): void {
  if (orgId) {
    localStorage.setItem(ORG_ID_KEY, orgId);
  } else {
    localStorage.removeItem(ORG_ID_KEY);
  }
}

/**
 * Bearer token storage (sessionStorage: per-tab, cleared when the tab
 * closes — smaller XSS exposure window than localStorage).
 *
 * The API returns `access_token` from /auth/login and /auth/company-signup.
 * Cross-origin SPA auth via HttpOnly cookies is fragile (SameSite + third-
 * party cookie policies drop the cookie in real browsers), so the console
 * rides the Authorization header instead; the cookie path remains as a
 * backend fallback (desktop app, websockets).
 */
export function getStoredToken(): string | null {
  if (typeof sessionStorage === 'undefined') return null;
  return sessionStorage.getItem(TOKEN_KEY);
}

export function setStoredToken(token: string | null): void {
  if (typeof sessionStorage === 'undefined') return;
  if (token) {
    sessionStorage.setItem(TOKEN_KEY, token);
  } else {
    sessionStorage.removeItem(TOKEN_KEY);
  }
}

export function clearAuthStorage(): void {
  localStorage.removeItem(ORG_ID_KEY);
  setStoredToken(null);
}

// NB-59: module-level soft-reset signal. The response interceptor clears
// auth storage and notifies subscribers; AuthContext nulls its state and
// ProtectedRoute performs the in-app redirect — no window.location bounce.
type SessionExpiredListener = () => void;

const sessionExpiredListeners = new Set<SessionExpiredListener>();

/** Registers a session-expired listener; returns an unsubscribe function. */
export function onAuthSessionExpired(listener: SessionExpiredListener): () => void {
  sessionExpiredListeners.add(listener);
  return () => {
    sessionExpiredListeners.delete(listener);
  };
}

// NB-59: while a session is being established (login POST → me →
// subscription), a refused follow-up request must not wipe the freshly
// issued token or bounce the operator — the login surface owns errors here.
let establishingSession = false;

export function beginAuthSessionEstablishment(): void {
  establishingSession = true;
}

export function endAuthSessionEstablishment(): void {
  establishingSession = false;
}

function hasAuthMaterial(): boolean {
  return Boolean(getStoredToken() || getStoredOrgId());
}

function notifySessionExpired(): void {
  sessionExpiredListeners.forEach((listener) => listener());
}

export const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 20000,
  withCredentials: true,
});

api.interceptors.request.use((config) => {
  const token = getStoredToken();
  if (token) {
    config.headers.set('Authorization', `Bearer ${token}`);
  }
  const orgId = getStoredOrgId();
  if (orgId) {
    config.headers.set('X-Organization-Id', orgId);
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    const status = error?.response?.status;
    if (status === 401 && !establishingSession && hasAuthMaterial()) {
      clearAuthStorage();
      notifySessionExpired();
    }
    return Promise.reject(error);
  },
);

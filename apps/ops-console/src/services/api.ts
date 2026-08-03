import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api/v1';

const TOKEN_KEY = 'supply_chain_token';
const ORG_ID_KEY = 'supply_chain_org_id';

export function getStoredToken(): string | null {
  return localStorage.getItem(TOKEN_KEY);
}

export function setStoredToken(token: string | null): void {
  if (token) {
    localStorage.setItem(TOKEN_KEY, token);
  } else {
    localStorage.removeItem(TOKEN_KEY);
  }
}

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

export function clearAuthStorage(): void {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(ORG_ID_KEY);
}

export const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 20000,
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
    if (status === 401) {
      clearAuthStorage();
      if (typeof window !== 'undefined' && window.location.pathname !== '/login') {
        window.location.assign('/login');
      }
    }
    return Promise.reject(error);
  },
);

import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react';

import { login as loginApi, logout as logoutApi, me as meApi } from '../services/authApi';
import { getCurrentSubscription } from '../services/billingApi';
import {
  clearAuthStorage,
  getStoredOrgId,
  getStoredToken,
  setStoredOrgId,
} from '../services/api';
import type { UserRead } from '../types/auth';

type AuthContextValue = {
  user: UserRead | null;
  orgId: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (identifier: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  getToken: () => Promise<string | null>;
};

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

let _cachedToken: string | null = null;

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<UserRead | null>(null);
  const [orgId, setOrgId] = useState<string | null>(getStoredOrgId());
  const [isLoading, setIsLoading] = useState(true);

  const getToken = useCallback(async (): Promise<string | null> => {
    const stored = getStoredToken();
    if (stored) return stored;
    try {
      const { data } = await import('../services/api').then((m) =>
        m.api.get<{ access_token: string }>('/auth/token'),
      );
      _cachedToken = data.access_token;
      return data.access_token;
    } catch {
      return null;
    }
  }, []);

  useEffect(() => {
    let cancelled = false;
    async function bootstrap() {
      try {
        const current = await meApi();
        if (cancelled) return;
        setUser(current);

        try {
          const sub = await getCurrentSubscription();
          if (!cancelled) {
            setOrgId(sub.organization_id);
            setStoredOrgId(sub.organization_id);
          }
        } catch {
          // org_id from stored value is fine
        }
      } catch {
        // not authenticated — no cookie present
        setUser(null);
        setOrgId(null);
      } finally {
        if (!cancelled) setIsLoading(false);
      }
    }
    bootstrap();
    return () => { cancelled = true; };
  }, []);

  const login = useCallback(async (identifier: string, password: string) => {
    await loginApi(identifier, password);
    const current = await meApi();
    setUser(current);
    try {
      const sub = await getCurrentSubscription();
      setOrgId(sub.organization_id);
      setStoredOrgId(sub.organization_id);
    } catch {
      // use any pre-existing org_id
    }
  }, []);

  const logout = useCallback(async () => {
    try {
      await logoutApi();
    } catch {
      // cookie might already be gone
    }
    clearAuthStorage();
    setUser(null);
    setOrgId(null);
  }, []);

  const value = useMemo(
    () => ({
      user,
      orgId,
      isAuthenticated: Boolean(user),
      isLoading,
      login,
      logout,
      getToken,
    }),
    [user, orgId, isLoading, login, logout, getToken],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
}

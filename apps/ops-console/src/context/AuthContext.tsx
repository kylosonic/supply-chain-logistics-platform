import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react';

import { login as loginApi, me as meApi } from '../services/authApi';
import { getCurrentSubscription } from '../services/billingApi';
import { clearAuthStorage, getStoredOrgId, getStoredToken, setStoredOrgId, setStoredToken } from '../services/api';
import type { UserRead } from '../types/auth';

type AuthContextValue = {
  token: string | null;
  user: UserRead | null;
  orgId: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (identifier: string, password: string) => Promise<void>;
  logout: () => void;
};

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [token, setToken] = useState<string | null>(getStoredToken());
  const [user, setUser] = useState<UserRead | null>(null);
  const [orgId, setOrgId] = useState<string | null>(getStoredOrgId());
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    async function bootstrap() {
      const currentToken = getStoredToken();
      if (!currentToken) {
        setIsLoading(false);
        return;
      }
      try {
        const current = await meApi(currentToken);
        if (cancelled) return;
        setUser(current);

        try {
          const sub = await getCurrentSubscription();
          if (!cancelled) {
            setOrgId(sub.organization_id);
            setStoredOrgId(sub.organization_id);
          }
        } catch {
          // subscription endpoint may be unavailable; org_id from stored value is fine
        }
      } catch {
        clearAuthStorage();
        setToken(null);
        setUser(null);
        setOrgId(null);
      } finally {
        if (!cancelled) setIsLoading(false);
      }
    }
    bootstrap();
    return () => { cancelled = true; };
  }, [token]);

  const login = useCallback(async (identifier: string, password: string) => {
    const data = await loginApi(identifier, password);
    setStoredToken(data.access_token);
    setToken(data.access_token);
    const current = await meApi(data.access_token);
    setUser(current);
    try {
      const sub = await getCurrentSubscription();
      setOrgId(sub.organization_id);
      setStoredOrgId(sub.organization_id);
    } catch {
      // use any pre-existing org_id
    }
  }, []);

  const logout = useCallback(() => {
    clearAuthStorage();
    setToken(null);
    setUser(null);
    setOrgId(null);
  }, []);

  const value = useMemo(
    () => ({
      token,
      user,
      orgId,
      isAuthenticated: Boolean(token && user),
      isLoading,
      login,
      logout,
    }),
    [token, user, orgId, isLoading, login, logout],
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

import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react';
import { useQueryClient } from '@tanstack/react-query';

import {
  getLiveSessionToken,
  login as loginApi,
  logout as logoutApi,
  me as meApi,
} from '../services/authApi';
import { getCurrentSubscription } from '../services/billingApi';
import {
  beginAuthSessionEstablishment,
  clearAuthStorage,
  endAuthSessionEstablishment,
  getStoredOrgId,
  getStoredToken,
  onAuthSessionExpired,
  setStoredOrgId,
} from '../services/api';
import type { UserRead } from '../types/auth';
import { clearLiveSession } from '../hooks/useLiveUpdates';
import { clearAllQueuedProofs } from '../services/driverProofQueue';

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

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const queryClient = useQueryClient();
  const [user, setUser] = useState<UserRead | null>(null);
  const [orgId, setOrgId] = useState<string | null>(getStoredOrgId());
  const [isLoading, setIsLoading] = useState(true);

  // soft session reset — the interceptor clears storage and fires
  // this signal; the provider only nulls state (single responsibility),
  // and ProtectedRoute performs the in-app redirect via <Navigate>.
  // Declared before the bootstrap effect so the listener exists before any
  // bootstrap-time 401 can fire.
  useEffect(() => {
    return onAuthSessionExpired(() => {
      setUser(null);
      setOrgId(null);
      queryClient.clear();
      clearLiveSession();
      void clearAllQueuedProofs().catch(() => undefined);
    });
  }, [queryClient]);

  // Stored-token-only: the token is written by login/signup in
  // authApi; there is no /auth/token refresh path to consult.
  const getToken = useCallback(async (): Promise<string | null> => {
    if (!getStoredToken()) return null;
    return getLiveSessionToken();
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
          // Never keep an old selected workspace when the new session cannot
          // prove its membership. A stale X-Organization-Id can only cause
          // 403s or point the console at the wrong workspace.
          setOrgId(null);
          setStoredOrgId(null);
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
    // the whole login POST → me → subscription sequence runs under
    // the establishment guard, so a refused follow-up request cannot wipe
    // the freshly issued token or soft-redirect mid-sign-in; errors surface
    // through the existing login catch instead.
    beginAuthSessionEstablishment();
    try {
      // Never let data from the previous account survive a workspace switch.
      queryClient.clear();
      clearLiveSession();
      setStoredOrgId(null);
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
    } finally {
      endAuthSessionEstablishment();
    }
  }, [queryClient]);

  const logout = useCallback(async () => {
    try {
      await logoutApi();
    } catch {
      // cookie might already be gone
    }
    clearAuthStorage();
    await clearAllQueuedProofs().catch(() => undefined);
    setUser(null);
    setOrgId(null);
    queryClient.clear();
    clearLiveSession();
    for (const key of Object.keys(localStorage)) {
      if (key.startsWith('freightpilot_driver_')) {
        localStorage.removeItem(key);
      }
    }
    if ('caches' in window) {
      void caches.keys().then((keys) =>
        Promise.all(keys.map((key) => caches.delete(key))),
      );
    }
  }, [queryClient]);

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

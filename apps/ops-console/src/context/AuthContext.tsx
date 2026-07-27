import { createContext, useContext, useEffect, useMemo, useState } from 'react';

import { login as loginApi, me as meApi } from '../services/authApi';
import type { UserRead } from '../types/auth';

type AuthContextValue = {
  token: string | null;
  user: UserRead | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (identifier: string, password: string) => Promise<void>;
  logout: () => void;
};

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

const TOKEN_KEY = 'supply_chain_token';

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [token, setToken] = useState<string | null>(localStorage.getItem(TOKEN_KEY));
  const [user, setUser] = useState<UserRead | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    async function bootstrap() {
      if (!token) {
        setIsLoading(false);
        return;
      }
      try {
        const current = await meApi(token);
        setUser(current);
      } catch {
        localStorage.removeItem(TOKEN_KEY);
        setToken(null);
        setUser(null);
      } finally {
        setIsLoading(false);
      }
    }
    bootstrap();
  }, [token]);

  async function login(identifier: string, password: string) {
    const data = await loginApi(identifier, password);
    localStorage.setItem(TOKEN_KEY, data.access_token);
    setToken(data.access_token);
    const current = await meApi(data.access_token);
    setUser(current);
  }

  function logout() {
    localStorage.removeItem(TOKEN_KEY);
    setToken(null);
    setUser(null);
  }

  const value = useMemo(
    () => ({ token, user, isAuthenticated: Boolean(token && user), isLoading, login, logout }),
    [token, user, isLoading],
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

import { api, setStoredToken } from './api';
import type { LoginResponse, UserRead } from '../types/auth';

export async function login(identifier: string, password: string): Promise<LoginResponse> {
  const { data } = await api.post<LoginResponse>('/auth/login', { identifier, password });
  setStoredToken(data.access_token);
  return data;
}

export async function register(username: string, password: string, role: 'admin' | 'operator' | 'viewer') {
  const { data } = await api.post('/auth/register', { username, password, role });
  return data;
}

export async function me(): Promise<UserRead> {
  const { data } = await api.get<UserRead>('/auth/me');
  return data;
}

export async function getLiveSessionToken(): Promise<string> {
  const { data } = await api.get<{ access_token: string }>('/auth/token');
  return data.access_token;
}

export async function logout(): Promise<void> {
  await api.post('/auth/logout');
}

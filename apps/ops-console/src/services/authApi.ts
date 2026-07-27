import { api } from './api';
import type { LoginResponse, UserRead } from '../types/auth';

export async function login(identifier: string, password: string): Promise<LoginResponse> {
  const { data } = await api.post<LoginResponse>('/auth/login', { identifier, password });
  return data;
}

export async function register(username: string, password: string, role: 'admin' | 'operator' | 'viewer') {
  const { data } = await api.post('/auth/register', { username, password, role });
  return data;
}

export async function me(token: string): Promise<UserRead> {
  const { data } = await api.get<UserRead>('/auth/me', {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });
  return data;
}

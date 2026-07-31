export type UserRole = 'admin' | 'owner' | 'operator' | 'viewer';

export type UserRead = {
  id: string;
  username: string;
  email?: string | null;
  full_name?: string | null;
  role: UserRole;
  is_active: boolean;
  created_at: string;
};

export type LoginResponse = {
  access_token: string;
  token_type: 'bearer';
  expires_in_seconds: number;
};

export type UserRole = 'admin' | 'operator' | 'viewer';

export type UserRead = {
  id: string;
  username: string;
  role: UserRole;
  is_active: boolean;
  created_at: string;
};

export type LoginResponse = {
  access_token: string;
  token_type: 'bearer';
  expires_in_seconds: number;
};

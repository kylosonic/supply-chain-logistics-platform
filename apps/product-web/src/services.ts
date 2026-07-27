export type SignupTier = 'starter' | 'scale' | 'enterprise';

export type CompanySignupRequest = {
  company_name: string;
  company_email: string;
  password: string;
  full_name?: string;
  subscription_tier: SignupTier;
};

export type CompanySignupResponse = {
  access_token: string;
  token_type: string;
  expires_in_seconds: number;
  user: {
    id: string;
    username: string;
    email: string | null;
    full_name: string | null;
    role: string;
    is_active: boolean;
    created_at: string;
  };
  organization: {
    id: string;
    name: string;
    slug: string;
    primary_email_domain: string | null;
    subscription_tier: SignupTier;
    subscription_status: string;
    created_at: string;
  };
};

const apiBase = import.meta.env.VITE_PLATFORM_API_URL || 'http://localhost:8000/api/v1';

export async function companySignup(payload: CompanySignupRequest): Promise<CompanySignupResponse> {
  const response = await fetch(`${apiBase}/auth/company-signup`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    const details = await response.text();
    throw new Error(details || 'Failed to create company account');
  }

  return (await response.json()) as CompanySignupResponse;
}

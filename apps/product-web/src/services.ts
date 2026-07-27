import { createClient } from '@supabase/supabase-js';

export type SignupTier = 'starter' | 'scale' | 'enterprise';

export type CompanySignupRequest = {
  company_name: string;
  company_email: string;
  password: string;
  full_name?: string;
  subscription_tier: SignupTier;
};

export type CompanySignupResponse = {
  mode: 'supabase' | 'platform-api';
  user_id: string;
  email: string;
  email_verification_required: boolean;
};

const apiBase = import.meta.env.VITE_PLATFORM_API_URL || 'http://localhost:8000/api/v1';
const supabaseUrl = import.meta.env.VITE_SUPABASE_URL as string | undefined;
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY as string | undefined;

const supabaseClient = supabaseUrl && supabaseAnonKey ? createClient(supabaseUrl, supabaseAnonKey) : null;

function normalizeError(details: string, fallback: string): string {
  const trimmed = details.trim();
  if (!trimmed) {
    return fallback;
  }

  if (trimmed.startsWith('{')) {
    try {
      const parsed = JSON.parse(trimmed) as { message?: string; error_description?: string; msg?: string };
      return parsed.message || parsed.error_description || parsed.msg || fallback;
    } catch {
      return trimmed;
    }
  }

  return trimmed;
}

async function signupWithSupabase(payload: CompanySignupRequest): Promise<CompanySignupResponse> {
  if (!supabaseClient) {
    throw new Error('Supabase client is not configured');
  }

  const { data, error } = await supabaseClient.auth.signUp({
    email: payload.company_email,
    password: payload.password,
    options: {
      data: {
        company_name: payload.company_name,
        full_name: payload.full_name ?? '',
        subscription_tier: payload.subscription_tier,
      },
    },
  });

  if (error) {
    throw new Error(error.message || 'Could not create account with Supabase auth');
  }

  if (!data.user) {
    throw new Error('Supabase did not return a user record');
  }

  if (data.session) {
    const { error: profileError } = await supabaseClient.from('company_profiles').upsert(
      {
        id: data.user.id,
        company_name: payload.company_name,
        company_email: payload.company_email,
        subscription_tier: payload.subscription_tier,
      },
      { onConflict: 'id' },
    );

    if (profileError) {
      throw new Error(profileError.message || 'Supabase profile setup failed');
    }
  }

  return {
    mode: 'supabase',
    user_id: data.user.id,
    email: payload.company_email,
    email_verification_required: !data.session,
  };
}

async function signupWithPlatformApi(payload: CompanySignupRequest): Promise<CompanySignupResponse> {
  const response = await fetch(`${apiBase}/auth/company-signup`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    const details = await response.text();
    throw new Error(normalizeError(details, 'Failed to create company account'));
  }

  const result = (await response.json()) as {
    user: { id: string; email: string | null };
  };

  return {
    mode: 'platform-api',
    user_id: result.user.id,
    email: result.user.email ?? payload.company_email,
    email_verification_required: false,
  };
}

export async function companySignup(payload: CompanySignupRequest): Promise<CompanySignupResponse> {
  if (supabaseClient) {
    return signupWithSupabase(payload);
  }

  return signupWithPlatformApi(payload);
}

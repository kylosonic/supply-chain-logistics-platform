import { networkFailureMessage } from './site-content';

export type SignupTier = 'starter' | 'scale' | 'enterprise';

export type CompanySignupRequest = {
  company_name: string;
  company_email: string;
  password: string;
  full_name?: string;
  subscription_tier?: SignupTier;
};

export type CompanySignupResponse = {
  user_id: string;
  email: string;
};

const apiBase = process.env.NEXT_PUBLIC_PLATFORM_API_URL || 'http://localhost:8000/api/v1';

/**
 * Extract the human-readable message from a FastAPI error body.
 *
 * FastAPI sends `{"detail": "..."}` for plain HTTPExceptions and
 * `{"detail": [{"loc": [...], "msg": "...", "type": "..."}]}` for 422
 * validation errors. Legacy shapes (`message` / `error_description` / `msg`)
 * are kept as a fallback only.
 */
function normalizeError(raw: string, fallback: string): string {
  const trimmed = raw.trim();
  if (!trimmed) {
    return fallback;
  }

  if (trimmed.startsWith('{')) {
    try {
      const parsed = JSON.parse(trimmed) as {
        detail?: unknown;
        message?: string;
        error_description?: string;
        msg?: string;
      };

      if (typeof parsed.detail === 'string' && parsed.detail.length > 0) {
        return parsed.detail;
      }

      if (Array.isArray(parsed.detail) && parsed.detail.length > 0) {
        const first = parsed.detail[0] as { msg?: string };
        if (typeof first?.msg === 'string' && first.msg.length > 0) {
          return first.msg;
        }
      }

      return parsed.message || parsed.error_description || parsed.msg || fallback;
    } catch {
      return trimmed;
    }
  }

  return trimmed;
}

export async function companySignup(payload: CompanySignupRequest): Promise<CompanySignupResponse> {
  let response: Response;
  try {
    response = await fetch(`${apiBase}/auth/company-signup`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(payload),
    });
  } catch {
    // Network failure (DNS, refused connection, offline).
    throw new Error(networkFailureMessage);
  }

  if (!response.ok) {
    const details = await response.text();
    throw new Error(normalizeError(details, 'Could not create the company workspace.'));
  }

  const result = (await response.json()) as {
    user: { id: string; email: string | null };
  };

  return {
    user_id: result.user.id,
    email: result.user.email ?? payload.company_email,
  };
}

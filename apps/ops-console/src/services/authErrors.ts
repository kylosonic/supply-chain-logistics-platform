/**
 * Friendly error mapping for the control-tower login page.
 *
 * The "Create initial admin" bootstrap (POST /auth/register) is only legal
 * when the platform has zero users. Once a workspace exists, the API returns
 * 401 "Admin authentication required" — which is correct backend behavior but
 * a trap for a real new admin who just signed up and is looking for the way
 * in. This module maps that specific API detail to guidance instead of
 * surfacing the raw string.
 */

export const ADMIN_ALREADY_EXISTS_MESSAGE =
  'This workspace already has an admin. Sign in with your company email and password above instead.';

export const ADMIN_ALREADY_EXISTS_DETAIL = 'Admin authentication required';

/** Extract the FastAPI `detail` field from an unknown error, if present. */
export function apiDetail(err: unknown): string | null {
  if (typeof err === 'object' && err !== null && 'response' in err) {
    const response = (err as { response?: { data?: { detail?: string } } }).response;
    if (response?.data?.detail) {
      return response.data.detail;
    }
  }
  if (err instanceof Error && err.message) {
    return err.message;
  }
  return null;
}

/**
 * Error message for the bootstrap action. Maps the "admin already exists"
 * 401 to actionable guidance; every other failure falls through to the raw
 * detail (or the fallback).
 */
export function bootstrapErrorMessage(err: unknown, fallback: string): string {
  const detail = apiDetail(err);
  if (detail === ADMIN_ALREADY_EXISTS_DETAIL) {
    return ADMIN_ALREADY_EXISTS_MESSAGE;
  }
  return detail ?? fallback;
}

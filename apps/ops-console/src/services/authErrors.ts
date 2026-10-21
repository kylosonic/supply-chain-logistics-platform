/**
 * Extract a human-readable message from an unknown API error.
 *
 * FastAPI has two `detail` shapes and both occur in production:
 *
 * - `{"detail": "..."}` for a raised `HTTPException`;
 * - `{"detail": [{loc, msg, type, input}, ...]}` for a 422 validation error.
 *
 * The second shape is an *object*, and returning it as-is made React render a
 * raw object as a child ("Objects are not valid as a React child (found:
 * object with keys {type, loc, msg, input})") — i.e. any 422 turned a form
 * error into a blank white page instead of a message. Both shapes are
 * flattened to a string here.
 */
export function apiDetail(err: unknown): string | null {
  if (typeof err === 'object' && err !== null && 'response' in err) {
    const response = (
      err as { response?: { data?: { detail?: unknown; message?: unknown } } }
    ).response;
    const detail = response?.data?.detail;

    if (typeof detail === 'string' && detail.length > 0) {
      return detail;
    }

    if (Array.isArray(detail)) {
      const messages = detail
        .map((entry) => {
          if (typeof entry === 'string') return entry;
          if (entry && typeof entry === 'object' && 'msg' in entry) {
            const { msg, loc } = entry as { msg?: unknown; loc?: unknown };
            const field = Array.isArray(loc) ? loc.filter((p) => p !== 'body').join('.') : '';
            if (typeof msg === 'string') {
              return field ? `${field}: ${msg}` : msg;
            }
          }
          return null;
        })
        .filter((m): m is string => Boolean(m));
      if (messages.length > 0) {
        return messages.join('; ');
      }
      return null;
    }

    if (typeof response?.data?.message === 'string' && response.data.message.length > 0) {
      return response.data.message;
    }
  }
  if (err instanceof Error && err.message) {
    return err.message;
  }
  return null;
}

/**
 * Message for a failed API call.
 *
 * The console surfaces the API's own `detail` string verbatim (the product's
 * honesty rule: no invented copy), falling back to the caller's text. Taking
 * `unknown` lets every `catch` block stay untyped instead of reaching for
 * `any`, which the lint gate rejects.
 */
export function apiErrorMessage(err: unknown, fallback: string): string {
  return apiDetail(err) ?? fallback;
}

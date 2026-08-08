import { useAuth } from '../../context/AuthContext';
import { publishLivePayload, useLiveUpdates } from '../../hooks/useLiveUpdates';

/**
 * TECH-73 (NB-56): the single live-socket owner for the workspace session.
 * Mounted once inside Layout so the connection opens once per authenticated
 * session and stays open while the operator works; the effect cleanup closes
 * it on logout and the next login opens a fresh one. Renders nothing.
 *
 * `getToken` is a stable useCallback from AuthContext, `Boolean(user)` gates
 * the socket exactly like the old dashboard call, and `publishLivePayload` is
 * a module-stable reference — no effect churn on layout re-renders.
 */
export function SessionLiveUpdates() {
  const { getToken, user } = useAuth();
  useLiveUpdates({ getToken, enabled: Boolean(user), onMessage: publishLivePayload });
  return null;
}

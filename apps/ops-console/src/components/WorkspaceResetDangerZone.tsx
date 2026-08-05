import { useState } from 'react';

import { Panel } from './ui/Panel';
import { useResetWorkspace } from '../hooks/queries';

/**
 * NB-35 admin-gated workspace reset: typed-confirmation modal only — no
 * keyboard shortcut, no light confirm (NB-35.6). The server re-validates
 * OWNER/ADMIN membership on POST /activation/reset (decision #10); the
 * console gates the surface on the global admin role for UX.
 *
 * On success the hook clears auth state, calls POST /auth/logout for the
 * cookie clear, and redirects to /login (NB-35.7).
 */
export function WorkspaceResetDangerZone({
  organizationName,
  isAdmin,
  defaultOpen = false,
}: {
  organizationName: string;
  isAdmin: boolean;
  defaultOpen?: boolean;
}) {
  const resetMutation = useResetWorkspace();
  const [resetModalOpen, setResetModalOpen] = useState(defaultOpen);
  const [typedWorkspaceName, setTypedWorkspaceName] = useState('');

  if (!isAdmin) return null;

  return (
    <Panel
      eyebrow="Danger zone"
      title="Reset workspace to sample data"
      description="Wipe every real CSV-uploaded row and restore the seeded sample workspace. This is nuclear and irreversible — the reset event is recorded in the audit timeline."
    >
      <button
        type="button"
        onClick={() => {
          setTypedWorkspaceName('');
          setResetModalOpen(true);
        }}
        className="glow-ring inline-flex min-h-11 items-center justify-center rounded-full border border-rose-500/40 px-5 text-sm font-semibold text-rose-200 transition hover:border-rose-400/60 hover:bg-rose-950/30"
      >
        Reset workspace to sample data
      </button>
      {resetMutation.isError ? (
        <p className="mt-3 text-sm text-rose-300">
          Reset failed: {(resetMutation.error as Error)?.message || 'Unknown error'}
        </p>
      ) : null}

      {resetModalOpen ? (
        <div
          className="fixed inset-0 z-50 grid place-items-center bg-black/60 p-4 backdrop-blur-sm"
          role="dialog"
          aria-modal="true"
        >
          <div className="w-full max-w-md rounded-[28px] border border-rose-500/30 bg-slate-950 p-6 shadow-[0_24px_80px_rgba(2,12,20,0.5)]">
            <h3 className="font-['Space_Grotesk'] text-xl font-semibold text-rose-100">
              Reset workspace to sample data?
            </h3>
            <p className="mt-2 text-sm leading-6 text-slate-400">
              All real uploaded data across warehouses, items, fleet assets, inventory, and orders
              will be deleted and replaced with the seeded sample set. Milestones reset to 0 of 5.
              Type <span className="font-semibold text-slate-100">{organizationName}</span> to
              confirm.
            </p>
            <input
              value={typedWorkspaceName}
              onChange={(event) => setTypedWorkspaceName(event.target.value)}
              placeholder={organizationName}
              aria-label="Workspace name confirmation"
              className="glow-ring mt-4 min-h-12 w-full rounded-2xl border border-slate-700 bg-slate-900/80 px-4 text-sm text-slate-100 outline-none transition focus:border-rose-400/50"
            />
            <div className="mt-5 flex flex-wrap justify-end gap-3">
              <button
                type="button"
                onClick={() => setResetModalOpen(false)}
                className="rounded-full border border-slate-700 px-4 py-2 text-sm font-semibold text-slate-300 transition hover:border-slate-500"
              >
                Cancel
              </button>
              <button
                type="button"
                disabled={typedWorkspaceName !== organizationName || resetMutation.isPending}
                onClick={() => resetMutation.mutate(typedWorkspaceName)}
                className="rounded-full border border-rose-500/50 bg-rose-950/30 px-4 py-2 text-sm font-semibold text-rose-100 transition hover:bg-rose-950/50 disabled:cursor-not-allowed disabled:opacity-50"
              >
                {resetMutation.isPending ? 'Resetting...' : 'Reset workspace'}
              </button>
            </div>
          </div>
        </div>
      ) : null}
    </Panel>
  );
}

import type { UserRead } from '../../types/auth';

type ShellHeaderProps = {
  contextLabel: string;
  descriptor: string;
  user: UserRead | null | undefined;
  onOpenNavigation: () => void;
};

export function ShellHeader({ contextLabel, descriptor, user, onOpenNavigation }: ShellHeaderProps) {
  return (
    <header className="fp-shell-surface px-4 py-4 sm:px-5">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-start gap-3">
          <button
            type="button"
            onClick={onOpenNavigation}
            className="inline-grid h-10 w-10 place-items-center rounded-[var(--fp-radius-panel)] border border-slate-700/70 bg-slate-950/75 text-slate-300 transition-colors hover:border-slate-500/80 hover:bg-slate-900/80 hover:text-slate-100 lg:hidden"
            aria-label="Open navigation"
          >
            <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M4 6h16M4 12h16M4 18h16" />
            </svg>
          </button>

          <div className="space-y-1">
            <p className="text-[11px] font-medium tracking-[0.18em] text-slate-500">{contextLabel}</p>
            <p className="text-sm leading-6 text-slate-300">{descriptor}</p>
          </div>
        </div>

        {user ? (
          <div className="flex flex-wrap items-center gap-2 text-xs text-slate-400">
            <span className="fp-pill font-mono uppercase tracking-[0.18em] text-slate-300">{user.role}</span>
            <span className="fp-pill text-slate-400">{user.email || user.username}</span>
          </div>
        ) : null}
      </div>
    </header>
  );
}

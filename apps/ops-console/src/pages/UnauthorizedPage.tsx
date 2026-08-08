export function UnauthorizedPage() {
  return (
    <div className="flex min-h-screen items-center justify-center p-6">
      <div className="fp-shell-surface animate-fade-in w-full max-w-md p-8 text-center">
        <h1 className="font-['Space_Grotesk'] text-2xl font-semibold tracking-tight text-slate-100">
          Unauthorized
        </h1>
        <p className="mt-2 text-sm leading-6 text-slate-400">You do not have permission to access this page.</p>
      </div>
    </div>
  );
}

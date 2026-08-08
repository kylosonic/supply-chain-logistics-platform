type LoginFeedbackPanelsProps = {
  signInError: string | null;
  bootstrapError: string | null;
};

function FeedbackPanel({
  testId,
  message,
}: {
  testId: string;
  message: string;
}) {
  return (
    <div
      data-testid={testId}
      className="rounded-[var(--fp-radius-panel)] border border-rose-500/25 bg-rose-950/30 px-3.5 py-3 text-sm text-rose-300"
    >
      {message}
    </div>
  );
}

export function LoginFeedbackPanels({ signInError, bootstrapError }: LoginFeedbackPanelsProps) {
  if (!signInError && !bootstrapError) {
    return null;
  }

  return (
    <div className="space-y-3">
      {signInError ? <FeedbackPanel testId="login-signin-error" message={signInError} /> : null}
      {bootstrapError ? <FeedbackPanel testId="login-bootstrap-error" message={bootstrapError} /> : null}
    </div>
  );
}

type LoginFeedbackPanelsProps = {
  signInError: string | null;
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

export function LoginFeedbackPanels({ signInError }: LoginFeedbackPanelsProps) {
  if (!signInError) {
    return null;
  }

  return (
    <div className="space-y-3">
      {signInError ? <FeedbackPanel testId="login-signin-error" message={signInError} /> : null}
    </div>
  );
}

import { renderToString } from 'react-dom/server';
import { describe, expect, it } from 'vitest';

import { LoginFeedbackPanels } from './LoginFeedbackPanels';

describe('LoginFeedbackPanels', () => {
  it('renders nothing when no feedback exists', () => {
    const html = renderToString(<LoginFeedbackPanels signInError={null} bootstrapError={null} />);

    expect(html).toBe('');
  });

  it('renders the sign-in error in its own surface', () => {
    const html = renderToString(
      <LoginFeedbackPanels signInError="Login failed" bootstrapError={null} />,
    );

    expect(html).toContain('data-testid="login-signin-error"');
    expect(html).toContain('Login failed');
    expect(html).not.toContain('data-testid="login-bootstrap-error"');
  });

  it('renders the bootstrap error in its own surface', () => {
    const html = renderToString(
      <LoginFeedbackPanels signInError={null} bootstrapError="Failed to create initial admin" />,
    );

    expect(html).toContain('data-testid="login-bootstrap-error"');
    expect(html).toContain('Failed to create initial admin');
    expect(html).not.toContain('data-testid="login-signin-error"');
  });

  it('renders both error channels as separate surfaces', () => {
    const html = renderToString(
      <LoginFeedbackPanels
        signInError="Login failed"
        bootstrapError="Failed to create initial admin"
      />,
    );

    expect(html).toContain('data-testid="login-signin-error"');
    expect(html).toContain('data-testid="login-bootstrap-error"');
    expect(html).toContain('Login failed');
    expect(html).toContain('Failed to create initial admin');
  });
});

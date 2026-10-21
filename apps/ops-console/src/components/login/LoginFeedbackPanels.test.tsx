import { renderToString } from 'react-dom/server';
import { describe, expect, it } from 'vitest';

import { LoginFeedbackPanels } from './LoginFeedbackPanels';

describe('LoginFeedbackPanels', () => {
  it('renders nothing when no feedback exists', () => {
    const html = renderToString(<LoginFeedbackPanels signInError={null} />);

    expect(html).toBe('');
  });

  it('renders the sign-in error in its own surface', () => {
    const html = renderToString(
      <LoginFeedbackPanels signInError="Login failed" />,
    );

    expect(html).toContain('data-testid="login-signin-error"');
    expect(html).toContain('Login failed');
    expect(html).not.toContain('login-bootstrap-error');
  });
});

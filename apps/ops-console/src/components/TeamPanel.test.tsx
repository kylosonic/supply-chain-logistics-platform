import { renderToString } from 'react-dom/server';
import { describe, expect, it, vi } from 'vitest';

import { TeamPanel } from './TeamPanel';

vi.mock('../context/AuthContext', () => ({
  useAuth: () => ({
    user: { role: 'admin', username: 'owner', email: 'owner@company.com' },
  }),
}));

vi.mock('../services/teamApi', () => ({
  getTeamMembers: vi.fn().mockResolvedValue([]),
  getInvitations: vi.fn().mockResolvedValue([]),
  createInvitation: vi.fn(),
  changeMemberRole: vi.fn(),
  removeMember: vi.fn(),
  revokeInvitation: vi.fn(),
}));

describe('team panel', () => {
  it('renders the invite flow and explains the link lifetime', () => {
    const html = renderToString(<TeamPanel />);

    expect(html).toContain('Invite the people who run the operation');
    expect(html).toContain('The invite link expires after 72 hours.');
    expect(html).toContain('Create invitation');
  });
});

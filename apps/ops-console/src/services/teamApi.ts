import { api } from './api';
import type {
  InvitationCreated,
  OrganizationInvitation,
  OrganizationMember,
  OrganizationRole,
} from '../types/api';
import type { LoginResponse, UserRead } from '../types/auth';

export type InviteRole = Exclude<OrganizationRole, 'owner'>;

export async function getTeamMembers(): Promise<OrganizationMember[]> {
  const { data } = await api.get<OrganizationMember[]>('/team/members');
  return data;
}

export async function getInvitations(): Promise<OrganizationInvitation[]> {
  const { data } = await api.get<OrganizationInvitation[]>('/team/invitations');
  return data;
}

export async function createInvitation(email: string, role: InviteRole): Promise<InvitationCreated> {
  const { data } = await api.post<InvitationCreated>('/team/invitations', { email, role });
  return data;
}

export async function revokeInvitation(invitationId: string): Promise<void> {
  await api.delete(`/team/invitations/${invitationId}`);
}

export async function changeMemberRole(
  membershipId: string,
  role: InviteRole,
): Promise<OrganizationMember> {
  const { data } = await api.patch<OrganizationMember>(`/team/members/${membershipId}`, { role });
  return data;
}

export async function removeMember(membershipId: string): Promise<void> {
  await api.delete(`/team/members/${membershipId}`);
}

export type InvitationAcceptResponse = LoginResponse & {
  user: UserRead;
  organization: { id: string; name: string };
  organization_role: OrganizationRole;
};

export async function acceptInvitation(payload: {
  token: string;
  username: string;
  password: string;
  full_name?: string;
}): Promise<InvitationAcceptResponse> {
  const { data } = await api.post<InvitationAcceptResponse>('/team/invitations/accept', payload);
  return data;
}

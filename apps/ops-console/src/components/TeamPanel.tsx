import { useEffect, useState } from 'react';

import { useAuth } from '../context/AuthContext';
import {
  changeMemberRole,
  createInvitation,
  getInvitations,
  getTeamMembers,
  removeMember,
  revokeInvitation,
  type InviteRole,
} from '../services/teamApi';
import { apiErrorMessage } from '../services/authErrors';
import type { OrganizationInvitation, OrganizationMember } from '../types/api';

const FIELD =
  'min-h-11 w-full rounded-lg border border-slate-700 bg-slate-950/70 px-3 text-sm text-slate-100 outline-none transition focus:border-sky-400';

export function TeamPanel() {
  const { user } = useAuth();
  const [members, setMembers] = useState<OrganizationMember[]>([]);
  const [invitations, setInvitations] = useState<OrganizationInvitation[]>([]);
  const [email, setEmail] = useState('');
  const [role, setRole] = useState<InviteRole>('operator');
  const [inviteLink, setInviteLink] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  async function refresh() {
    try {
      const [nextMembers, nextInvitations] = await Promise.all([getTeamMembers(), getInvitations()]);
      setMembers(nextMembers);
      setInvitations(nextInvitations);
      setError(null);
    } catch (err) {
      setError(apiErrorMessage(err, 'Could not load workspace members.'));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    if (user?.role === 'admin') void refresh();
  }, [user?.role]);

  if (user?.role !== 'admin') {
    return (
      <section className="fp-shell-surface p-5">
        <p className="text-sm text-slate-400">
          Workspace owners and admins can manage teammates. Ask an admin if you need access.
        </p>
      </section>
    );
  }

  async function onInvite(event: React.FormEvent) {
    event.preventDefault();
    setError(null);
    setInviteLink(null);
    try {
      const created = await createInvitation(email, role);
      setInviteLink(created.invite_url);
      setEmail('');
      await refresh();
    } catch (err) {
      setError(apiErrorMessage(err, 'Could not create the invitation.'));
    }
  }

  async function onRoleChange(member: OrganizationMember, nextRole: InviteRole) {
    try {
      const updated = await changeMemberRole(member.membership_id, nextRole);
      setMembers((current) =>
        current.map((item) => (item.membership_id === updated.membership_id ? updated : item)),
      );
    } catch (err) {
      setError(apiErrorMessage(err, 'Could not change the member role.'));
    }
  }

  async function onRemove(member: OrganizationMember) {
    if (!window.confirm(`Remove ${member.username} from this workspace?`)) return;
    try {
      await removeMember(member.membership_id);
      await refresh();
    } catch (err) {
      setError(apiErrorMessage(err, 'Could not remove the member.'));
    }
  }

  async function onRevoke(invitation: OrganizationInvitation) {
    try {
      await revokeInvitation(invitation.id);
      await refresh();
    } catch (err) {
      setError(apiErrorMessage(err, 'Could not revoke the invitation.'));
    }
  }

  return (
    <section className="space-y-5">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <p className="text-xs font-medium uppercase tracking-[0.18em] text-sky-300">Workspace team</p>
          <h2 className="mt-2 font-['Space_Grotesk'] text-2xl font-semibold text-slate-50">
            Invite the people who run the operation
          </h2>
          <p className="mt-2 max-w-2xl text-sm leading-7 text-slate-400">
            Invitations are attached to this workspace only. The invite link expires after 72 hours.
            An existing account must use its current password.
          </p>
        </div>
        <button
          type="button"
          onClick={() => void refresh()}
          className="rounded-full border border-slate-700 px-4 py-2 text-xs font-semibold text-slate-300 hover:border-slate-500"
        >
          Refresh
        </button>
      </div>

      {error ? <p className="rounded-lg border border-rose-500/25 bg-rose-950/25 p-3 text-sm text-rose-200">{error}</p> : null}

      <form onSubmit={onInvite} className="fp-nested-surface grid gap-3 p-4 md:grid-cols-[1fr_180px_auto]">
        <label className="grid gap-1.5 text-xs text-slate-400">
          Email
          <input
            className={FIELD}
            type="email"
            required
            value={email}
            onChange={(event) => setEmail(event.target.value)}
            placeholder="teammate@company.com"
          />
        </label>
        <label className="grid gap-1.5 text-xs text-slate-400">
          Role
          <select className={FIELD} value={role} onChange={(event) => setRole(event.target.value as InviteRole)}>
            <option value="viewer">Viewer</option>
            <option value="operator">Operator</option>
            <option value="admin">Admin</option>
          </select>
        </label>
        <button className="self-end rounded-lg bg-sky-500 px-5 py-3 text-sm font-semibold text-slate-950 hover:bg-sky-400">
          Create invitation
        </button>
      </form>

      {inviteLink ? (
        <div className="rounded-lg border border-emerald-500/25 bg-emerald-950/25 p-4">
          <p className="text-sm font-semibold text-emerald-100">Invitation created</p>
          <p className="mt-1 text-xs text-emerald-200/70">
            No email is sent yet. Copy this one-time link and share it securely.
          </p>
          <code className="mt-3 block break-all rounded bg-slate-950/60 p-3 text-xs text-emerald-100">{inviteLink}</code>
        </div>
      ) : null}

      <div className="grid gap-5 lg:grid-cols-2">
        <div className="fp-nested-surface p-4">
          <h3 className="font-['Space_Grotesk'] text-lg font-semibold text-slate-100">Members</h3>
          <div className="mt-3 space-y-2">
            {loading ? <p className="text-sm text-slate-500">Loading members…</p> : null}
            {members.map((member) => (
              <div key={member.membership_id} className="rounded-lg border border-slate-800 p-3">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <div>
                    <p className="text-sm font-semibold text-slate-100">{member.full_name || member.username}</p>
                    <p className="text-xs text-slate-500">{member.email || member.username}</p>
                  </div>
                  <div className="flex items-center gap-2">
                    {member.role === 'owner' ? (
                      <span className="text-xs font-semibold text-amber-200">Owner</span>
                    ) : (
                      <select
                        className="rounded border border-slate-700 bg-slate-950 px-2 py-1 text-xs text-slate-200"
                        value={member.role}
                        onChange={(event) => void onRoleChange(member, event.target.value as InviteRole)}
                      >
                        <option value="viewer">Viewer</option>
                        <option value="operator">Operator</option>
                        <option value="admin">Admin</option>
                      </select>
                    )}
                    {member.username !== user.username && member.role !== 'owner' ? (
                      <button
                        type="button"
                        onClick={() => void onRemove(member)}
                        className="text-xs text-rose-300 hover:text-rose-200"
                      >
                        Remove
                      </button>
                    ) : null}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="fp-nested-surface p-4">
          <h3 className="font-['Space_Grotesk'] text-lg font-semibold text-slate-100">Pending invitations</h3>
          <div className="mt-3 space-y-2">
            {invitations.filter((item) => item.status === 'pending').length === 0 ? (
              <p className="text-sm text-slate-500">No pending invitations.</p>
            ) : null}
            {invitations
              .filter((item) => item.status === 'pending')
              .map((invitation) => (
                <div
                  key={invitation.id}
                  className="flex items-center justify-between gap-3 rounded-lg border border-slate-800 p-3"
                >
                  <div>
                    <p className="text-sm text-slate-100">{invitation.email}</p>
                    <p className="text-xs text-slate-500">
                      {invitation.role} · expires {new Date(invitation.expires_at).toLocaleString()}
                    </p>
                  </div>
                  <button
                    type="button"
                    onClick={() => void onRevoke(invitation)}
                    className="text-xs text-rose-300 hover:text-rose-200"
                  >
                    Revoke
                  </button>
                </div>
              ))}
          </div>
        </div>
      </div>
    </section>
  );
}

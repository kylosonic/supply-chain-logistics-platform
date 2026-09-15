# Swarm Operating Health & v1.1 Growth Candidates — Living Behaviors

> 🟡 **PARTIALLY DONE — v1.1 growth features DEFERRED by product decision (2026-09-14).** No `feat/swarm-health-growth-v1` branch was opened: release-blocking security and launch tickets took priority. Every rule below is written from the user's perspective (state, actions, consequences), not implementation mechanics.
>
> **Satisfied incidentally:**
> - **NB-80** (state file exists and is current) — `docs/swarm/STATE.md` exists, records phase/branch/tickets/gates/risks/evidence, and was updated at every gate transition this batch.
> - **NB-82** (deployment topology recorded as an ADR) — `docs/adr/0001-production-database-topology.md`.
>
> **Still open:** NB-81 (no merge without recorded human UAT — the *rule* is documented but no merged batch has exercised it yet), and NB-83..NB-85 (teammate invites, phone-on-file visibility, route explanations) which were explicitly deferred and are not started.

## 1. Why this feature exists

Two kinds of gaps remain after the security-hardening and launch-readiness batches:

1. **Swarm operating health.** The engineering swarm's own operating system (AGENTS.md) mandates a state file (`docs/swarm/STATE.md`) that does not exist, and its merge protocol requires explicit human UAT approval that the ledger has not always recorded. The system that builds the product must itself be trustworthy and observable.
2. **v1.1 growth candidates.** The product register promises a team workspace, but there is no way for an owner to invite teammates; the escalation-SMS behavior (NB-16) can silently fail when no phone is on file; and the route planner gives no explanation for why a route was chosen — the kind of question every serious dispatcher asks.

## 2. The actors and their roles

- **Owner / Admin:** invites teammates into the workspace by email; sees the workspace's phone-on-file state and its consequences.
- **New teammate:** accepts an invite, signs in, and operates inside the company workspace with the role the owner assigned.
- **Operator:** sees a clear warning before an escalation SMS could fail; asks "why this route?" and gets a concrete answer.
- **Engineering swarm (@architect, @qa, @vision):** operates from a current state file; merges only with recorded human UAT.
- **System:** enforces invite state, surfaces phone-on-file state, and produces route rationale.

## 3. Swarm operating health (OPS)

### 3.1 The swarm state file exists and is current (NB-80)

- `docs/swarm/STATE.md` exists and records: current phase (from `INTAKE → … → DEPLOYED`), active feature branch, open TECH tickets, completed/failed gates, retry counts, unresolved risks, artifact paths, and last verification evidence.
- The architect updates it at every gate transition; stale state is a defect.

### 3.2 No merge without recorded human UAT (NB-81)

- Every batch's closeout records explicit human UAT approval (what was checked, by whom, when) in the ledger before merge to `master`.
- A batch whose ledger says "awaiting human UAT" is never merged until the approval entry exists.
- This applies from the next merged batch onward, including the security-hardening and launch-readiness batches.

### 3.3 Deployment topology is a recorded decision (NB-82)

- The Supabase-as-Postgres vs. VPS-Postgres decision from `docs/production-readiness-plan.md` §1 is resolved and recorded as an ADR, including the retirement notes for the path not taken.
- No deployment documentation contradicts the ADR.

## 4. v1.1 growth candidates (GR)

### 4.1 Owners can invite teammates (NB-83)

When an owner or admin opens the account page:

- they see an "Invite teammate" action; entering a teammate's email sends an invitation (or, for v1.1-minimum, creates the member record with a role assignment);
- the invited person signs in and operates inside the same workspace with the assigned role (owner / admin / operator / viewer);
- role assignments respect the existing org-role machinery: an invite can never grant a global role, and a viewer invite can never write;
- the owner sees who is in the workspace and can change roles or remove a member;
- acceptance and removal are reflected immediately in the member's next session, without a full reload.

**Failure outcome:** an invite that never arrives, or a role that silently grants more than intended, blocks this ticket.

### 4.2 Phone-on-file state is visible before it matters (NB-84)

- The account page shows whether a contact phone is on file for the workspace, in the same surface where escalation behavior is explained.
- When no phone is on file, the workspace shows a clear, non-dismissible warning on the receipts/escalation surface: "No phone on file — escalation messages cannot reach you by SMS. Add a phone in Account."
- When a phone is added, the warning disappears and the escalation path (NB-16) works end to end.

### 4.3 Route decisions are explainable (NB-85)

- After a route optimization completes, the operator can open a per-run "why this route" summary that states, in plain language, the dominant factors behind the plan (e.g., distance vs. time vs. cost vs. capacity vs. weather-risk weighting) and the runner-up alternative.
- The summary is derived from the actual run inputs, never fabricated; if no meaningful explanation exists for a run, the surface says so honestly (per the product's honesty rules).
- The explanation surface loads within the existing weight and performance budgets.

## 5. Preservation rules

- Nothing here changes existing locked behaviors (NB-01..79) or their acceptance criteria.
- Invites and roles reuse the existing org/membership machinery — no new global-role path.
- Route explanation never fabricates reasoning; it follows the honesty rules (NB-43).

## 6. Acceptance standard

This feature is complete when:

- `docs/swarm/STATE.md` exists, is current, and the ledger records explicit human UAT for every merged batch from this point forward;
- the deployment topology decision is recorded in an ADR and no doc contradicts it;
- an owner can invite a teammate who then operates with exactly the assigned role;
- phone-on-file state is visible on the account surface and the escalation warning appears before a silent SMS failure;
- every completed route optimization offers an honest "why this route" summary;
- the full test suites stay green.

---

## Ticket map

| Ticket | Rule |
|---|---|
| NB-80 | §3.1 The swarm state file exists and is current (OPS-01) |
| NB-81 | §3.2 No merge without recorded human UAT (OPS-02) |
| NB-82 | §3.3 Deployment topology is a recorded decision (OPS-03) |
| NB-83 | §4.1 Owners can invite teammates (GR-01) |
| NB-84 | §4.2 Phone-on-file state is visible before it matters (GR-02) |
| NB-85 | §4.3 Route decisions are explainable (GR-03) |

**Sources:** `AGENTS.md` §3 (state file) and §10 (UAT rule); `docs/desktop-b2b-roadmap.md` (team membership); `docs/behaviors/cashflow-bank-transfer-receipt-verification.md` NB-16 (escalation SMS); `docs/production-readiness-plan.md` §1 (topology decision).

# ADR-0001: Production database topology — Supabase-hosted Postgres, Supabase Auth retired

- **Status:** Accepted
- **Date:** 2026-09-14
- **Deciders:** Founder (product owner)
- **Supersedes:** the open decision recorded in `docs/production-readiness-plan.md` §1
- **Tickets:** NB-67 (Supabase auth), NB-82 (deployment topology as a recorded decision), NB-78

---

## 1. Context

The platform needs a managed Postgres in production. Two hosting paths were left open in
`docs/production-readiness-plan.md` §1:

- **(a) Supabase-hosted Postgres** — the existing linked project, reachable over the pooler.
- **(b) VPS-hosted Postgres** — a self-managed instance with our own backups.

Separately, the repository carried a `supabase/` directory written when Supabase **Auth** was the
planned identity provider for the product website. That plan was abandoned: the platform's own
FastAPI service now owns identity end to end (signup, login, JWT issuance as an HttpOnly
`SameSite=strict` cookie, roles, organisation memberships).

The 2026-08-10 security audit (finding **H-6**) recorded the abandoned Supabase auth configuration
as a landmine: email confirmations disabled, minimum password length 6, no complexity requirement,
`secure_password_change = false`, and no CAPTCHA. Connecting it to a signup flow again would have
shipped all of that.

## 2. Decision

**Postgres:** path **(a)** — the application's database is the Supabase-hosted Postgres, reached over
the connection pooler. `DATABASE_URL` is supplied per environment (locally via `.env`, in production
by the host's encrypted environment variables) and never committed.

**Auth:** Supabase Auth is **retired**, not hardened. The `supabase/` directory is marked retired in
`supabase/RETIRED.md` with the six conditions that would have to be met before it could be re-armed.
The `@supabase/supabase-js` client dependency was removed from `apps/product-web`.

**Schema ownership:** the application's own Alembic chain (`apps/platform-api/alembic/versions/`) is
the single source of truth for the operational schema. The one Supabase migration
(`supabase/migrations/20260727153410_company_onboarding_and_profiles.sql`) is applied history for the
legacy `company_profiles` table and its `auth.uid()`-scoped RLS policies; it is not used by the
application and must not be extended.

## 3. Consequences

**Positive**

- One identity system, owned by the application. No second auth surface to keep hardened, and no
  split between RLS-based and membership-based authorisation.
- Managed backups, PITR availability, and no VM to patch for the database.
- Tenant isolation is enforced in one place (`app/core/tenant_scope.py` plus membership checks) and
  pinned by a two-organisation regression suite, rather than split across RLS policies and
  application code.
- Removing the unused client dependency removes a supply-chain surface from the shipped website.

**Negative / accepted risks**

- **The database password is a single point of failure for environment portability.** It is stored
  only in the host's encrypted environment variables and is not recoverable from the repository. If
  it is lost, it must be rotated in the Supabase dashboard and re-set in every environment. This ADR
  is the record that this is a known, accepted operational dependency — not an oversight.
- Production schema changes depend on the Alembic chain running against the hosted database
  (`python -m alembic upgrade head`), so a failed migration is a production incident rather than a
  local-only event.
- Path **(b)** is not maintained. Migrating to a self-hosted Postgres later requires a dump/restore
  and a re-point of `DATABASE_URL`; no code change is needed because the application only knows a
  SQLAlchemy URL.

**Retirement notes for the path not taken (path b)**

- No VPS is provisioned and no self-managed Postgres configuration exists to maintain.
- `scripts/db_backup.ps1` / `db_restore.ps1` / `db_backup.sh` / `db_restore.sh` remain in the
  repository and work against any Postgres URL, so they also serve as the restore-drill tooling for
  the chosen path.

## 4. Compliance with other documents

- `docs/behaviors/production-security-hardening.md` §7 (NB-67) — satisfied: the Supabase auth path is
  retired and documented.
- `docs/behaviors/swarm-health-and-growth-candidates.md` §3.3 (NB-82) — satisfied: this ADR is the
  recorded topology decision.
- `docs/production-readiness-plan.md` §1 — the open decision referenced there is now closed by this
  ADR. Any statement in that document that still presents the choice as open is historical.
- `README.md` — updated to describe Supabase as the managed Postgres host and to stop describing
  Supabase auth as an active path.

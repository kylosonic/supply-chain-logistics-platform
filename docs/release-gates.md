# Release Gates (NB-77)

**Purpose:** define what must be green before a change reaches production, and how the deploy is
actually blocked when it is not. Written because a release gate that cannot fail is documentation,
not a gate.

---

## 1. The gates

Every push to `master`/`main` and every pull request request runs `.github/workflows/ci.yml`, which
executes the same commands a release depends on — not a subset.

| Job | Gates | Blocks |
|---|---|---|
| `backend-tests` | Install from `apps/platform-api/requirements.lock` with `--require-hashes`; `pytest -q --timeout=120 -n 4`; `ruff check app` | Any backend defect or lint regression |
| `backend-dependency-audit` | `pip-audit -r requirements.lock --strict` | A known-vulnerable pinned dependency |
| `ops-console` | `npm ci`; `npm run typecheck`; `npm run lint` (`--max-warnings=0`); `npm run test`; `npm run build`; `npm audit --audit-level=high` | Console type errors, lint errors, test failures, build failures, vulnerable production dependencies |
| `product-web` | `npm ci`; `npm run test`; `npm run build`; `npm run check:bundle`; `npm audit --audit-level=high` | Site test/build failures, page-weight budget breach, vulnerable production dependencies |

Local equivalents, run before pushing:

```bash
# backend (from apps/platform-api)
python -m pytest -q --timeout=120 -n 4
ruff check app

# ops console (from repo root)
npm --prefix apps/ops-console run typecheck
npm --prefix apps/ops-console run lint
npm --prefix apps/ops-console run test
npm --prefix apps/ops-console run build

# product web (from repo root)
npm --prefix apps/product-web run test
npm --prefix apps/product-web run build
npm --prefix apps/product-web run check:bundle
```

## 2. Why the backend installs from the lockfile

`pip install -e .` resolves open `>=` ranges, so CI would test a *different* dependency set from the
one Docker deploys. `requirements.lock` is generated from `pyproject.toml` and hash-pinned:

```bash
# regenerate after changing pyproject.toml dependencies
uv pip compile pyproject.toml --generate-hashes --python-version 3.12 --output-file requirements.lock
```

The Dockerfile installs `--require-hashes -r requirements.lock`, so a fresh image cannot resolve an
unpatched transitive dependency. CI installs the same file, which is what makes the test result
evidence about the deployed artefact.

## 3. How a red gate blocks the deploy

Vercel deploys on push. To make CI authoritative, **one** of the following must be configured. Until
one is, a red CI run does not stop a Vercel production deploy.

### Option A — Vercel "Ignored Build Step" (per project, recommended)

For each Vercel project (`product-web`, `ops-console`, `platform-api`):

1. Vercel dashboard → project → **Settings** → **Git**.
2. Enable **Ignored Build Step** and use **Run a command**:

```bash
git log -1 --pretty=%B | grep -qE '\[skip ci\]|\[vercel skip\]'
```

This skips the build only when the commit explicitly opts out. It does **not** by itself wait for CI.

### Option B — GitHub branch protection (the real block)

1. GitHub → repository → **Settings** → **Branches** → add a branch protection rule for `master`.
2. Enable **Require status checks to pass before merging**.
3. Select `backend-tests`, `backend-dependency-audit`, `ops-console`, `product-web`.
4. Enable **Require branches to be up to date before merging**.

With this in place, no change reaches `master` while any gate is red — and because Vercel deploys
from `master`, a red gate cannot reach production. **This is the configuration that makes the gate
authoritative**; Option A alone does not.

### Option C — Vercel deployment checks (Pro/Enterprise)

Vercel dashboard → project → **Settings** → **Git** → **Deployment Checks**: register the GitHub
Actions workflow as a required check. Vercel then holds the deployment until the check reports.

> **Current status (honest):** the workflow is committed and runs, and all four jobs pass on a green
> tree. The branch-protection rule in Option B has **not** been confirmed as enabled. Until it is,
> treat CI as a strong signal rather than a hard block, and do not merge with a red run.

## 4. Dependency advisories: production vs development

`npm audit --audit-level=high` runs **without** `--omit=dev`, so dev-only tooling advisories also
fail the gate. The current known dev-only advisories are tracked in
`docs/adr/tech-backlog.md`. The release contract
(`docs/behaviors/production-security-hardening.md` §6) is about **deployed** surfaces; if a
dev-only advisory blocks an urgent release, switch that job to `npm audit --omit=dev --audit-level=high`
and record the dev-only items in the backlog rather than silently lowering the level.

## 5. Release checklist

Before merging to `master`:

- [ ] All four CI jobs green on the branch
- [ ] `docs/swarm/STATE.md` updated (phase, branch, gates, evidence)
- [ ] Behaviour documentation updated if user-visible behaviour changed
- [ ] Security-relevant change reviewed against `docs/security-audit-2026-08-10.md`
- [ ] Explicit human UAT recorded in the ledger (NB-81: no merge without it)
- [ ] Rollback path stated (previous Vercel deployment can be promoted; DB migrations are additive)

After deploying to production:

- [ ] `GET /health` reports `{"status":"ok","db":"ok"}`
- [ ] Signup funnel reachable end to end (`docs/eaii/submission-checklist.md` Part E notes the
      current production database blocker)
- [ ] No new error spike in the deployment's runtime logs

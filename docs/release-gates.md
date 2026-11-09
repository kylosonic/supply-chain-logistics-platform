# Release Gates

A change is ready to merge when the checks in `.github/workflows/ci.yml` pass. The workflow runs on pushes and pull requests to `master` and `main`.

## CI jobs

| Job | Checks |
| --- | --- |
| `backend-tests` | Hash-pinned Python install, full pytest suite, Ruff syntax and undefined-name checks |
| `backend-dependency-audit` | `pip-audit` against `requirements.lock` |
| `ops-console` | Clean install, typecheck, lint, tests, production build, deployed-dependency audit |
| `product-web` | Clean install, tests, production build, bundle budget, deployed-dependency audit |
| `desktop` | Clean install, archive-path tests, Electron runtime check, dependency audit |

The npm applications are installed independently from their per-application lockfiles. The repository root intentionally has no workspace lockfile.

## Local gate

Run the commands in [README.md](../README.md#tests-and-checks) before pushing.

## Deployment blocking

Vercel deploys changes from `master`. Configure GitHub branch protection to require every CI job before a pull request can merge. Until that rule is enabled, CI is visible but does not itself prevent a direct push from deploying.

Alternatively, register the CI jobs as required Vercel deployment checks. A red job must hold the deployment rather than merely notify the team.

## Dependency advisories

The deployed-set npm audits use `--omit=dev`. Development-only advisories are visible in the non-blocking audit step. A high or critical advisory in code shipped to users blocks the release.

## Release checklist

Before merging:

- All CI jobs pass.
- User-visible behavior changes are documented.
- Security-sensitive changes include regression tests.
- A rollback path is known.
- Any database migration has been tested forward and backward where the migration can be reversed.

After deploying:

- `GET /health` returns `{"status":"ok","db":"ok"}`.
- The product site and operations console load.
- The production smoke workflow passes.
- Runtime logs show no new error spike.

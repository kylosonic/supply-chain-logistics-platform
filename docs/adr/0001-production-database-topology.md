# Production database topology

- Status: accepted
- Date: 2026-09-16

## Decision

Production uses managed PostgreSQL on Neon, reached through its pooled connection endpoint. `DATABASE_URL` is supplied by the deployment environment and is not committed.

FreightPilot's FastAPI service owns authentication and authorization. The application does not depend on a separate hosted authentication or data API.

## Schema ownership

The Alembic chain in `apps/platform-api/alembic/versions/` is the source of truth for the operational schema. Deployments apply migrations with `python -m alembic upgrade head`.

## Consequences

- Managed backups and point-in-time recovery are provided by the database host.
- Database credentials must be rotated and configured in every deployment environment.
- Tenant isolation is enforced in application code and covered by cross-organization tests.
- Moving to another PostgreSQL host requires a dump and restore, followed by a `DATABASE_URL` change.

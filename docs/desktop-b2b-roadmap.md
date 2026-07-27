# Desktop B2B Roadmap (Suggested Next Additions)

This repository now includes the monorepo structure needed to scale to a B2B desktop SaaS platform.

## Core architecture additions

1. Multi-tenant organizations
- Add `organizations` table and scope all business data by `organization_id`.
- Introduce team membership with roles: owner, admin, dispatcher, viewer.

2. Bring-your-own-key (BYOK) vault
- Add encrypted storage for provider credentials per organization.
- Support key masking, revoke, and rotation flows.
- Store encrypted secrets only; never expose raw keys in logs or API responses.

3. Provider adapter layer
- Add adapter interfaces for OpenAI-compatible, Azure OpenAI, Anthropic-compatible endpoints.
- Normalize requests/responses to one internal contract.

4. Desktop packaging and updates
- Add desktop shell app (Electron or Tauri) under `apps/desktop`.
- Implement signed installers, secure update channel, and environment-specific release tracks.

5. Auditability and compliance
- Add `audit_events` for key changes, login activity, routing runs, and permission updates.
- Add retention policy and export endpoints for enterprise audits.

## Product website additions

1. Company signup flow with onboarding checklist.
2. Team invitation and seat management.
3. Download center for installers per OS and version channel.
4. Public docs for API key setup and provider-specific examples.
5. Trust and security pages (encryption, tenant boundaries, availability targets).

## AI optimization quality additions

1. Enrich risk model with weather severity, route closure, conflict, and customs delay feeds.
2. Add explainability endpoint that returns why a route was selected.
3. Add fallback routing strategy for provider outage or risk feed outage.
4. Add simulation mode to compare route plans by objective and constraints.

## Operational additions

1. Usage metering by org, seat, and optimization runs.
2. Billing plans and feature flags by subscription tier.
3. SSO (SAML/OIDC) for enterprise accounts.
4. Per-tenant observability dashboards.

## Recommended rollout sequence

1. Multi-tenant model and org auth.
2. BYOK vault and provider adapter layer.
3. Desktop shell with authenticated company login.
4. Metering, billing, and enterprise governance.
5. Advanced optimization and explainability.

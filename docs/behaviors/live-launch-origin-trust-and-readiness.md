# Live Launch — Origin Trust, Data Access Continuity & Deployment Hygiene — Living Behaviors

> ⚠️ **NOT YET IMPLEMENTED** — Locked in on 2026-08-07 following the pre-launch operational review. Every rule below is written from the user's perspective (state, actions, consequences), not implementation mechanics. Pending execution by `@build`/`@fixer` and verification by `@qa` against tickets NB-48 through NB-53 in the gap ledger.

## 1. Why this feature exists

The live platform is reachable at two official web addresses: the customer-facing site and the operator console. Both must be able to reach the platform, and the platform must be able to reach its own data store. Today, the browser's security pre-check fails from at least one of the two addresses, which blocks the launch flow entirely. This feature defines the rules that keep the live platform reachable from both addresses, keep its data access continuous through credential changes, and make the launch flow verifiable end-to-end.

## 2. The actors and their roles

- **Visitor:** a person opening the customer-facing site in a browser. Expects every page interaction to work without security-blocked errors.
- **Operator:** a person using the ops console. Expects the console to load and show live data from the same platform the visitor uses.
- **Maintainer:** the person or team performing configuration, credential, or code changes to the live platform. Operates under the sequencing rules in §5.
- **System (the live platform):** serves both official addresses, holds the customer data, and reports its own health honestly.

## 3. Origin trust

**3.1 — Both official web addresses are trusted.** When a visitor opens the customer-facing site (https://product-web-chi.vercel.app) or the operator opens the console (https://ops-console-azure.vercel.app), every request the page makes to the platform is accepted. The page never shows a browser security-blocked error.

**3.2 — The trust response names the requesting address.** The security acknowledgment returned to a page echoes the address the request came from. It is never pinned to one address — both official addresses are covered by the same rule, and a change for one must never silently break the other.

**3.3 — The platform accepts requests addressed to its own public address.** The platform never refuses a request for being unrecognized, including direct requests to its own public address. Both official web addresses can reach the platform by that address.

**3.4 — The trust list is a closed list, not an open door.** Any address not on the official list continues to be blocked. Adding an address is an explicit, deliberate act.

## 4. Data access continuity

**4.1 — Credential rotation never interrupts the live product.** When the connection secret for the data store is rotated, the platform's health indicator must not show the data store as unreachable at any point during the change.

**4.2 — Rollback is always possible.** At any moment during a rotation, the maintainer can restore the previous connection secret. A failed change is undone, not debugged at the customer's expense.

**4.3 — Every consumer is inventoried before rotation.** Before rotating, the maintainer lists every tool that connects to the data store (local development, migration tooling, smoke tests). After rotation, each one still connects successfully. Nothing breaks silently for a week.

**4.4 — Health confirms within 60 seconds.** Once the new secret is in place, the health indicator reports the data store reachable (`db: ok`) within 60 seconds.

## 5. Deployment sequencing

**5.1 — Configuration before code.** Origin-trust configuration (§3) must be live and verified before any new product code is published. The two are never published for the first time in the same moment.

**5.2 — Each change is verified independently.** Configuration changes and code changes are each verified on their own before the next step happens.

**5.3 — No regressions after publication.** Immediately after any code publication, the trust rules (§3) still pass and the health indicator still reports the data store reachable (§4).

## 6. Workspace hygiene

**6.1 — Full removal.** A removed workspace (such as a smoke-test workspace) no longer appears anywhere in the ops console, and no orphaned records from it remain anywhere in the system.

**6.2 — Review before removal.** Before any removal, the maintainer reviews a complete listing of the records that will be removed. The listing must contain only the intended workspace's data — never customer data.

**6.3 — No collateral damage.** Removing a workspace never affects any other workspace or customer record.

## 7. End-to-end launch verification

**7.1 — The launch flow is the site's single job (per the Site Conversion & Copy behavior doc §3):** the visitor clicked "Start free" and landed in the ops console with an authenticated session and a sample-data-seeded workspace.

**7.2 — The flow is verified from both official addresses.** A real browser session on each address completes the flow with no security-blocked requests, and the resulting workspace is visible from the operator's address.

**7.3 — Verification runs last.** The end-to-end verification happens only after the trust rules (§3), data access continuity (§4), code publication (§5), and workspace hygiene (§6) are all complete and verified.

## 8. Acceptance gate

The rules in this document are tracked as `P0` tickets NB-48 through NB-53 in the gap ledger. The launch flow is not considered operational until `@qa` has verified each ticket against its user-acceptance criteria.

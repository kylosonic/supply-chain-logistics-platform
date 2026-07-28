# Competitive Landscape and Overhaul Rationale (2026)

## Scope
This note captures publicly stated positioning and proof patterns from major logistics and last-mile platforms, then maps those patterns to the FreightPilot website and desktop onboarding overhaul.

Sources reviewed:
- Onfleet home and customer proof sections
- project44 platform and outcome sections
- FourKites home platform messaging
- Route4Me home and platform sections
- FarEye home and case-study highlights
- Shippeo home and trust sections
- Bringg home and platform sections

## Evidence Snapshot

| Company | Public proof signals found | Positioning pattern observed |
| --- | --- | --- |
| Onfleet | 400M+ deliveries; 99% on-time, 45% fuel savings, 50% fewer failed deliveries; 150+ courier partners; enterprise badges and ratings | Proof-first hero, then modular capability blocks (visibility, CX, automation, courier network) |
| project44 | $16M cost avoided case, $12M annual savings case, 99% detention reduction, 86% gate wait reduction, 72% faster exception response; 3.7T data points, 700M+ daily events | Financial outcomes + network scale + decision-intelligence narrative |
| FourKites | 85% exceptions auto-resolved; 1.1M carriers and suppliers; 3.2M daily shipments; 1,600+ businesses | AI-agent workforce framing with autonomous resolution emphasis |
| Route4Me | 3B+ miles optimized, 750M+ destinations, 30M+ routes, 40K+ customers; broad case-study footprint | Category authority through volume metrics and extensive social proof |
| FarEye | Case highlights including 36% growth and major labor-hour savings examples | Transformation language supported by customer result stories |
| Shippeo | Leader recognition in visibility category; SLA-centric positioning for tracking completeness and delay prediction | Trust and delivery assurance messaging (accuracy, onboarding, support) |
| Bringg | Modular platform + network + services framing; 250+ carrier solutions in 70+ countries claim | Enterprise orchestration messaging across owned, 3PL, and hybrid fleets |

## What Changed in FreightPilot

### Product website
Implemented in [apps/product-web/src/App.tsx](apps/product-web/src/App.tsx) and [apps/product-web/src/index.css](apps/product-web/src/index.css):

1. Added a dedicated competitive evidence section with named benchmark signals.
2. Shifted hero narrative from feature-first to proof-led operating model language.
3. Introduced a Detect-Decide-Act operating loop to mirror modern decision-intelligence framing.
4. Strengthened trust/governance presentation with explicit control cards.
5. Refined pricing interaction to support direct plan selection and ROI coupling.
6. Kept and expanded cash-flow-oriented ROI logic to foreground margin protection.
7. Preserved live signup behavior while tightening onboarding copy around launch readiness.

### Desktop onboarding
Implemented in [apps/desktop/src/onboarding.html](apps/desktop/src/onboarding.html), [apps/desktop/src/onboarding.css](apps/desktop/src/onboarding.css), and [apps/desktop/src/main.cjs](apps/desktop/src/main.cjs):

1. Upgraded onboarding into a launch cockpit with readiness scoring.
2. Added explicit role sign-off checkpoints (dispatch, data, security ownership).
3. Expanded wizard milestones from setup-only to setup plus operational go-live.
4. Added blocker/risk visibility to reduce hidden rollout gaps.
5. Preserved existing setup actions (save config, connectivity test, launch console, open links).

## Design Principles Applied

1. Proof before promise.
2. Operational outcomes over generic AI claims.
3. Cash-flow and margin clarity in commercial storytelling.
4. Trust and governance visible at first glance.
5. Faster time-to-live through role-aware onboarding.

## Notes

- Claims listed above are based on publicly presented website content captured during research and should be re-validated periodically.
- FreightPilot sections intentionally distinguish between benchmark patterns and FreightPilot-specific capabilities to avoid implying third-party metrics as internal results.

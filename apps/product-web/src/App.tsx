import { FormEvent, useMemo, useState } from 'react';

import { companySignup, type SignupTier } from './services';

type SignalMetric = {
  value: string;
  label: string;
  detail: string;
};

type PlatformFamily = {
  tag: string;
  title: string;
  summary: string;
  bullets: string[];
};

type WorkflowPhase = {
  title: string;
  detail: string;
  actions: string[];
};

type OutcomeTarget = {
  title: string;
  baseline: string;
  target: string;
  impact: string;
};

type TrustMarker = {
  title: string;
  detail: string;
};

type DeploymentStep = {
  title: string;
  detail: string;
};

type Plan = {
  tier: SignupTier;
  name: string;
  price: string;
  summary: string;
  bullets: string[];
  monthlyPriceUsd: number | null;
};

const signalMetrics: SignalMetric[] = [
  {
    value: 'Desktop',
    label: 'Operator-first launch',
    detail: 'Dispatch teams move from account creation to live workspace readiness in one guided flow.',
  },
  {
    value: 'BYOK',
    label: 'AI governance',
    detail: 'Provider keys stay customer-controlled with masking, preference management, and revoke paths.',
  },
  {
    value: 'Live',
    label: 'Exception cadence',
    detail: 'Routes, shipments, alerts, and planning are designed to work as one operating loop.',
  },
  {
    value: 'Usage',
    label: 'Margin guardrails',
    detail: 'Task metering and overage awareness are visible before costs turn into surprises.',
  },
];

const platformFamilies: PlatformFamily[] = [
  {
    tag: 'Control Tower',
    title: 'See the operation the way a regional operator actually runs it.',
    summary:
      'FreightPilot pulls route health, inventory pressure, shipment status, and exception load into one operational picture instead of scattering those decisions across separate tools.',
    bullets: ['Exception-led dispatching', 'Cross-workflow visibility', 'Role-aware surfaces'],
  },
  {
    tag: 'Decision Studio',
    title: 'Decide with route, cost, and service impact in the same frame.',
    summary:
      'Optimization is only useful when operators can compare tradeoffs quickly. FreightPilot keeps route logic, cost assumptions, and action consequences legible under pressure.',
    bullets: ['Scenario-aware routing', 'Cost-sensitive execution', 'Actionable delivery tradeoffs'],
  },
  {
    tag: 'Launch Cockpit',
    title: 'Go live with operator ownership instead of a forgotten checklist.',
    summary:
      'Desktop onboarding tracks readiness, validates environment setup, and makes role sign-off explicit so rollout risk is visible before first dispatch.',
    bullets: ['Readiness scoring', 'Role sign-off workflow', 'Environment validation'],
  },
  {
    tag: 'Revenue Guard',
    title: 'Protect margin where logistics software usually stops counting.',
    summary:
      'FreightPilot connects execution quality to failed-delivery loss, exception burden, and platform usage so the team sees what is actually costing money.',
    bullets: ['Task metering', 'Failure-loss modeling', 'Commercial visibility'],
  },
];

const workflow: WorkflowPhase[] = [
  {
    title: 'Detect',
    detail: 'Surface risk before it becomes a customer escalation or margin hit.',
    actions: ['Live alert queue', 'Shipment status drift', 'Inventory pressure cues'],
  },
  {
    title: 'Decide',
    detail: 'Compare route and service actions with cost and readiness context still visible.',
    actions: ['Optimization runs', 'Constraint-aware planning', 'Go-live ownership checks'],
  },
  {
    title: 'Act',
    detail: 'Move from decision to execution without losing auditability or role clarity.',
    actions: ['Operator handoff', 'Customer-facing follow-through', 'Usage and action traceability'],
  },
];

const outcomeTargets: OutcomeTarget[] = [
  {
    title: 'Exception response speed',
    baseline: 'Reactive triage, inbox chasing, and unclear ownership when the route starts drifting.',
    target: 'A prioritized queue with visible severity, owner expectation, and next action.',
    impact: 'Lower SLA miss risk and fewer disruptions left to age in the background.',
  },
  {
    title: 'Route margin visibility',
    baseline: 'Routing, delivery cost, and service recovery burden split across disconnected views.',
    target: 'One control surface that ties optimization, failure cost, and usage pressure together.',
    impact: 'Faster intervention on the workflows that quietly destroy contribution margin.',
  },
  {
    title: 'Launch readiness',
    baseline: 'Ad hoc onboarding with hidden blockers across security, data setup, and dispatch ownership.',
    target: 'Desktop launch readiness with role sign-off, connection checks, and milestone completion in one place.',
    impact: 'Shorter time from account creation to first reliable production dispatch cycle.',
  },
];

const trustMarkers: TrustMarker[] = [
  {
    title: 'Organization-scoped tenancy',
    detail: 'Company workspaces, subscriptions, AI preferences, and access are bounded to the tenant by design.',
  },
  {
    title: 'Provider key lifecycle',
    detail: 'Keys can be added, masked, tested, revoked, and assigned as the preferred provider without exposing raw secrets in the UI.',
  },
  {
    title: 'Operator-grade access control',
    detail: 'Admins, operators, viewers, and rollout owners can be given responsibility without giving everyone the same blast radius.',
  },
  {
    title: 'Usage-aware commercial controls',
    detail: 'Plans, included task limits, and overage visibility are surfaced as part of normal operations.',
  },
];

const deploymentSteps: DeploymentStep[] = [
  {
    title: 'Provision the workspace',
    detail: 'Create the company account, set the operating tier, and assign the launch owner.',
  },
  {
    title: 'Prepare the desktop crew',
    detail: 'Install the launch cockpit, verify production URLs, and test control tower connectivity from dispatch machines.',
  },
  {
    title: 'Wire governance and data',
    detail: 'Connect provider keys, assign roles, and import warehouse, fleet, inventory, and order data in sequence.',
  },
  {
    title: 'Run the first live window',
    detail: 'Dry-run routing, confirm readiness checkpoints, then open the control tower for live execution.',
  },
];

const plans: Plan[] = [
  {
    tier: 'starter',
    name: 'Starter',
    price: '$399/mo',
    summary: 'Single-region teams replacing reactive dispatch with a structured control tower.',
    bullets: ['Up to 25 active vehicles', '3 workspace users', '2,500 optimized tasks per month'],
    monthlyPriceUsd: 399,
  },
  {
    tier: 'scale',
    name: 'Scale',
    price: '$1,290/mo',
    summary: 'Growing operators standardizing exception playbooks and multi-region execution rhythms.',
    bullets: ['Up to 250 active vehicles', '20 workspace users', '5,000 optimized tasks per month'],
    monthlyPriceUsd: 1290,
  },
  {
    tier: 'enterprise',
    name: 'Enterprise',
    price: 'Custom',
    summary: 'Advanced governance, rollout support, and operating model control for large programs.',
    bullets: ['Unlimited vehicles and regions', 'Dedicated onboarding pod', 'Private deployment options'],
    monthlyPriceUsd: null,
  },
];

const heroSignals = [
  {
    label: 'Critical exception',
    title: 'SH-402 delivery window drifting by 27 min',
    tone: 'critical',
    detail: 'Recommended action: reroute after depot stop and notify consignee now.',
  },
  {
    label: 'Margin watch',
    title: 'Route cost variance trending +8.4%',
    tone: 'warning',
    detail: 'Fuel exposure and failed-delivery risk are stacking on the same lane.',
  },
  {
    label: 'Inventory pressure',
    title: 'AX-14 below safety stock in West Hub',
    tone: 'neutral',
    detail: 'Replenishment suggestion ready for approval before tomorrow morning wave.',
  },
  {
    label: 'Launch readiness',
    title: '2 role sign-offs still open',
    tone: 'neutral',
    detail: 'Security owner and dispatch lead need confirmation before go-live window opens.',
  },
];

const downloadUrl = import.meta.env.VITE_DESKTOP_DOWNLOAD_URL || 'https://example.com/download';
const docsUrl = import.meta.env.VITE_DOCS_URL || 'https://example.com/docs';
const appUrl = import.meta.env.VITE_APP_CONSOLE_URL || 'http://localhost';

export default function App() {
  const [companyName, setCompanyName] = useState('');
  const [companyEmail, setCompanyEmail] = useState('');
  const [fullName, setFullName] = useState('');
  const [password, setPassword] = useState('');
  const [tier, setTier] = useState<SignupTier>('starter');
  const [monthlyTasks, setMonthlyTasks] = useState(5000);
  const [avgDeliveryCost, setAvgDeliveryCost] = useState(18);
  const [optimizationSavingsRate, setOptimizationSavingsRate] = useState(12);
  const [failedDeliveryRate, setFailedDeliveryRate] = useState(6);
  const [costPerFailedDelivery, setCostPerFailedDelivery] = useState(24);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [statusMessage, setStatusMessage] = useState<string | null>(null);

  const selectedPlan = useMemo(() => plans.find((plan) => plan.tier === tier) ?? plans[0], [tier]);

  const roi = useMemo(() => {
    const safeTasks = Math.max(monthlyTasks, 0);
    const safeCost = Math.max(avgDeliveryCost, 0);
    const safeSavingsRate = Math.min(Math.max(optimizationSavingsRate, 0), 45);
    const safeFailedRate = Math.min(Math.max(failedDeliveryRate, 0), 100);
    const safeFailedCost = Math.max(costPerFailedDelivery, 0);

    const monthlySpend = safeTasks * safeCost;
    const optimizationSavings = monthlySpend * (safeSavingsRate / 100);
    const failedDeliveries = safeTasks * (safeFailedRate / 100);
    const assumedFailureReductionRate = 30;
    const failureSavings = failedDeliveries * safeFailedCost * (assumedFailureReductionRate / 100);
    const grossMonthlySavings = optimizationSavings + failureSavings;
    const platformCost = selectedPlan.monthlyPriceUsd ?? 0;
    const netMonthlyGain = grossMonthlySavings - platformCost;
    const annualNetGain = netMonthlyGain * 12;
    const paybackDays =
      platformCost > 0 && grossMonthlySavings > 0 ? Math.max(1, Math.ceil((platformCost / grossMonthlySavings) * 30)) : null;

    return {
      monthlySpend,
      optimizationSavings,
      failureSavings,
      grossMonthlySavings,
      platformCost,
      netMonthlyGain,
      annualNetGain,
      paybackDays,
      assumedFailureReductionRate,
    };
  }, [
    avgDeliveryCost,
    costPerFailedDelivery,
    failedDeliveryRate,
    monthlyTasks,
    optimizationSavingsRate,
    selectedPlan.monthlyPriceUsd,
  ]);

  const signupAndOpenApp = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setStatusMessage(null);
    setIsSubmitting(true);

    try {
      const result = await companySignup({
        company_name: companyName,
        company_email: companyEmail,
        password,
        full_name: fullName || undefined,
        subscription_tier: tier,
      });

      if (result.email_verification_required) {
        setStatusMessage(
          'Workspace created. Verify the company email, then continue in the desktop launch cockpit to finish rollout.',
        );
      } else {
        setStatusMessage('Workspace created. Your operators can now launch the desktop cockpit and begin readiness checks.');
      }

      setCompanyName('');
      setCompanyEmail('');
      setFullName('');
      setPassword('');
    } catch (error) {
      setStatusMessage(error instanceof Error ? error.message : 'Could not create company account.');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="web-shell">
      <header className="topbar">
        <a href="#top" className="brand" aria-label="FreightPilot home">
          <span className="brand-mark">FP</span>
          <span className="brand-copy">
            <strong>FreightPilot</strong>
            <span>Decision intelligence for delivery operations</span>
          </span>
        </a>

        <nav className="topnav" aria-label="Primary">
          <a href="#platform">Platform</a>
          <a href="#workflow">Workflow</a>
          <a href="#pricing">Pricing</a>
          <a href="#roi">ROI</a>
          <a href="#signup">Launch</a>
        </nav>

        <div className="topbar-actions">
          <a className="btn btn-ghost" href={docsUrl} target="_blank" rel="noreferrer">
            View docs
          </a>
          <a className="btn btn-primary" href={appUrl} target="_blank" rel="noreferrer">
            Open control tower
          </a>
        </div>
      </header>

      <main id="top">
        <section className="hero-panel">
          <div className="hero-copy">
            <p className="eyebrow">FreightPilot Control Stack</p>
            <h1>Decision intelligence for teams that cannot afford reactive dispatch.</h1>
            <p className="hero-lead">
              FreightPilot turns route execution, exception management, replenishment pressure, rollout readiness, and AI
              governance into one operating rhythm built for regional logistics teams and enterprise launch programs.
            </p>

            <div className="hero-actions">
              <a className="btn btn-primary" href="#signup">
                Create workspace
              </a>
              <a className="btn btn-secondary" href={downloadUrl} target="_blank" rel="noreferrer">
                Download desktop cockpit
              </a>
            </div>

            <p className="hero-note">
              Designed around the patterns category leaders use to win: operational proof, modular platform packaging,
              enterprise trust, and faster operator execution.
            </p>

            <div className="signal-grid" aria-label="Operating signals">
              {signalMetrics.map((metric) => (
                <article className="signal-card" key={metric.label}>
                  <span className="signal-value">{metric.value}</span>
                  <h2>{metric.label}</h2>
                  <p>{metric.detail}</p>
                </article>
              ))}
            </div>
          </div>

          <aside className="hero-console" aria-label="Live control tower preview">
            <div className="console-head">
              <div>
                <p className="eyebrow">Control preview</p>
                <h2>What operators watch before margin slips away.</h2>
              </div>
              <span className="console-pill">Live rhythm</span>
            </div>

            <div className="console-stack">
              {heroSignals.map((signal) => (
                <article className="console-row" key={signal.title}>
                  <div className={`tone-chip tone-${signal.tone}`}>{signal.label}</div>
                  <div className="console-copy">
                    <h3>{signal.title}</h3>
                    <p>{signal.detail}</p>
                  </div>
                </article>
              ))}
            </div>

            <div className="console-footer">
              <div>
                <span>Workspace sequence</span>
                <strong>Signup to desktop to data to live dispatch</strong>
              </div>
              <div>
                <span>Commercial model</span>
                <strong>Tiered subscription + usage visibility</strong>
              </div>
            </div>
          </aside>
        </section>

        <section id="platform" className="content-panel">
          <div className="section-copy">
            <p className="eyebrow">Platform families</p>
            <h2>One product, four decision layers, zero operator guesswork.</h2>
            <p>
              FreightPilot is packaged like a modern logistics platform, but shaped around the practical reality of ops:
              routing, alerts, planning, rollout, and governance must work together or the tool becomes shelfware.
            </p>
          </div>

          <div className="family-grid">
            {platformFamilies.map((family) => (
              <article className="family-card" key={family.title}>
                <span className="tag-chip">{family.tag}</span>
                <h3>{family.title}</h3>
                <p>{family.summary}</p>
                <ul>
                  {family.bullets.map((bullet) => (
                    <li key={bullet}>{bullet}</li>
                  ))}
                </ul>
              </article>
            ))}
          </div>
        </section>

        <section id="workflow" className="content-panel alt-panel">
          <div className="section-copy narrow-copy">
            <p className="eyebrow">Operator workflow</p>
            <h2>Detect, decide, and act in one repeatable motion.</h2>
          </div>

          <div className="workflow-grid">
            {workflow.map((phase) => (
              <article className="workflow-card" key={phase.title}>
                <h3>{phase.title}</h3>
                <p>{phase.detail}</p>
                <ul>
                  {phase.actions.map((action) => (
                    <li key={action}>{action}</li>
                  ))}
                </ul>
              </article>
            ))}
          </div>
        </section>

        <section className="split-band">
          <div className="content-panel">
            <div className="section-copy narrow-copy">
              <p className="eyebrow">Operational outcomes</p>
              <h2>Move from disconnected workflows to a control model that protects cash flow.</h2>
            </div>

            <div className="outcome-grid">
              {outcomeTargets.map((outcome) => (
                <article className="outcome-card" key={outcome.title}>
                  <h3>{outcome.title}</h3>
                  <p className="label">Before</p>
                  <p>{outcome.baseline}</p>
                  <p className="label">After</p>
                  <p>{outcome.target}</p>
                  <p className="impact-copy">Impact: {outcome.impact}</p>
                </article>
              ))}
            </div>
          </div>

          <div className="content-panel alt-panel">
            <div className="section-copy narrow-copy">
              <p className="eyebrow">Trust and launch</p>
              <h2>Enterprise controls should accelerate rollout, not slow it down.</h2>
            </div>

            <div className="trust-grid">
              {trustMarkers.map((marker) => (
                <article className="trust-card" key={marker.title}>
                  <h3>{marker.title}</h3>
                  <p>{marker.detail}</p>
                </article>
              ))}
            </div>

            <div className="launch-track">
              <h3>Deployment track</h3>
              <ol>
                {deploymentSteps.map((step) => (
                  <li key={step.title}>
                    <strong>{step.title}</strong>
                    <span>{step.detail}</span>
                  </li>
                ))}
              </ol>
            </div>
          </div>
        </section>

        <section id="pricing" className="content-panel">
          <div className="section-copy">
            <p className="eyebrow">Packaging</p>
            <h2>Transparent entry tiers with room for advanced operating programs.</h2>
            <p>
              Start with a task-based subscription, then scale into rollout support, governance depth, and larger fleet
              footprints as the operation matures.
            </p>
          </div>

          <div className="pricing-grid">
            {plans.map((plan) => (
              <article className={`pricing-card ${tier === plan.tier ? 'selected' : ''}`} key={plan.name}>
                <div className="pricing-head">
                  <span className="tag-chip">{plan.name}</span>
                  <p className="price-copy">{plan.price}</p>
                </div>
                <h3>{plan.summary}</h3>
                <ul>
                  {plan.bullets.map((bullet) => (
                    <li key={bullet}>{bullet}</li>
                  ))}
                </ul>
                <button
                  className="btn btn-plan"
                  type="button"
                  onClick={() => setTier(plan.tier)}
                  aria-pressed={tier === plan.tier}
                >
                  {tier === plan.tier ? 'Selected for ROI model' : `Model ${plan.name}`}
                </button>
              </article>
            ))}
          </div>
        </section>

        <section id="roi" className="split-band">
          <div className="content-panel">
            <div className="section-copy narrow-copy">
              <p className="eyebrow">ROI estimator</p>
              <h2>Model the commercial case before procurement or rollout approval.</h2>
              <p>
                FreightPilot keeps the argument tied to route savings, failure reduction, and task-aware pricing instead
                of vague transformation promises.
              </p>
            </div>

            <form className="roi-form" onSubmit={(event) => event.preventDefault()}>
              <label>
                Monthly optimized tasks
                <input
                  type="number"
                  min={0}
                  value={monthlyTasks}
                  onChange={(event) => setMonthlyTasks(Number(event.target.value))}
                />
              </label>
              <label>
                Average cost per delivery (USD)
                <input
                  type="number"
                  min={0}
                  step="0.01"
                  value={avgDeliveryCost}
                  onChange={(event) => setAvgDeliveryCost(Number(event.target.value))}
                />
              </label>
              <label>
                Route optimization savings rate (%)
                <input
                  type="number"
                  min={0}
                  max={45}
                  value={optimizationSavingsRate}
                  onChange={(event) => setOptimizationSavingsRate(Number(event.target.value))}
                />
              </label>
              <label>
                Failed delivery rate (%)
                <input
                  type="number"
                  min={0}
                  max={100}
                  value={failedDeliveryRate}
                  onChange={(event) => setFailedDeliveryRate(Number(event.target.value))}
                />
              </label>
              <label>
                Cost per failed delivery (USD)
                <input
                  type="number"
                  min={0}
                  step="0.01"
                  value={costPerFailedDelivery}
                  onChange={(event) => setCostPerFailedDelivery(Number(event.target.value))}
                />
              </label>
            </form>
          </div>

          <aside className="content-panel alt-panel roi-panel" aria-label="ROI results">
            <p className="eyebrow">Modeled result</p>
            <h2>{selectedPlan.name} operating model</h2>
            <ul>
              <li>
                <span>Monthly spend baseline</span>
                <strong>${roi.monthlySpend.toLocaleString()}</strong>
              </li>
              <li>
                <span>Route efficiency savings</span>
                <strong>${roi.optimizationSavings.toLocaleString()}</strong>
              </li>
              <li>
                <span>Failed-delivery savings</span>
                <strong>${roi.failureSavings.toLocaleString()}</strong>
              </li>
              <li>
                <span>Gross monthly savings</span>
                <strong>${roi.grossMonthlySavings.toLocaleString()}</strong>
              </li>
              <li>
                <span>Platform cost</span>
                <strong>${roi.platformCost.toLocaleString()}</strong>
              </li>
              <li>
                <span>Net monthly gain</span>
                <strong>${roi.netMonthlyGain.toLocaleString()}</strong>
              </li>
              <li>
                <span>Annual net gain</span>
                <strong>${roi.annualNetGain.toLocaleString()}</strong>
              </li>
              <li>
                <span>Estimated payback</span>
                <strong>{roi.paybackDays ? `${roi.paybackDays} days` : 'Custom plan review'}</strong>
              </li>
            </ul>
            <p className="hero-note">
              Model assumes a {roi.assumedFailureReductionRate}% reduction in failed-delivery incidents as a conservative
              planning baseline.
            </p>
          </aside>
        </section>

        <section id="signup" className="split-band">
          <div className="content-panel alt-panel">
            <div className="section-copy narrow-copy">
              <p className="eyebrow">Company launch</p>
              <h2>Create the workspace, then move straight into rollout readiness.</h2>
              <p>
                The launch sequence is designed to feel operational from the first click: account creation, desktop
                installation, control tower validation, role sign-off, and first live dispatch window.
              </p>
            </div>

            <div className="launch-actions">
              <a className="btn btn-secondary" href={downloadUrl} target="_blank" rel="noreferrer">
                Get desktop cockpit
              </a>
              <a className="btn btn-ghost" href={docsUrl} target="_blank" rel="noreferrer">
                Review rollout docs
              </a>
            </div>
          </div>

          <form className="content-panel signup-form" onSubmit={signupAndOpenApp}>
            <div className="section-copy narrow-copy">
              <p className="eyebrow">Workspace creation</p>
              <h2>Start the rollout.</h2>
            </div>

            <label>
              Company name
              <input required value={companyName} onChange={(event) => setCompanyName(event.target.value)} />
            </label>
            <label>
              Company email
              <input
                required
                type="email"
                value={companyEmail}
                onChange={(event) => setCompanyEmail(event.target.value)}
              />
            </label>
            <label>
              Launch owner name
              <input value={fullName} onChange={(event) => setFullName(event.target.value)} />
            </label>
            <label>
              Password
              <input
                required
                type="password"
                minLength={8}
                value={password}
                onChange={(event) => setPassword(event.target.value)}
              />
            </label>
            <label>
              Subscription tier
              <select value={tier} onChange={(event) => setTier(event.target.value as SignupTier)}>
                <option value="starter">Starter</option>
                <option value="scale">Scale</option>
                <option value="enterprise">Enterprise</option>
              </select>
            </label>
            <button className="btn btn-primary" type="submit" disabled={isSubmitting}>
              {isSubmitting ? 'Creating workspace...' : 'Create company workspace'}
            </button>
            {statusMessage ? <p className="status-note">{statusMessage}</p> : null}
          </form>
        </section>

        <section className="closing-panel">
          <div>
            <p className="eyebrow">Final point of view</p>
            <h2>FreightPilot is built to help operators act earlier, launch faster, and protect margin more deliberately.</h2>
          </div>
          <div className="hero-actions">
            <a className="btn btn-primary" href="#signup">
              Start company setup
            </a>
            <a className="btn btn-secondary" href={appUrl} target="_blank" rel="noreferrer">
              Open the app
            </a>
          </div>
        </section>
      </main>
    </div>
  );
}

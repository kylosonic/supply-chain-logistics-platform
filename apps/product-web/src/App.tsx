import { FormEvent, useMemo, useState } from 'react';

import { companySignup, type SignupTier } from './services';

type Capability = {
  title: string;
  detail: string;
  impact: string;
};

type WorkflowPhase = {
  title: string;
  detail: string;
  actions: string[];
};

type BenchmarkSignal = {
  company: string;
  signal: string;
  pattern: string;
};

type TrustMarker = {
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

type OutcomeTarget = {
  title: string;
  baseline: string;
  target: string;
  impact: string;
};

const capabilities: Capability[] = [
  {
    title: 'Decision control tower',
    detail:
      'Unify weather risk, inventory pressure, and route constraints into one desktop-first command surface built for dispatchers and operations leads.',
    impact: 'Fewer context switches when disruption windows are short.',
  },
  {
    title: 'Bring-your-own AI architecture',
    detail:
      'Keep your model strategy in your own hands. Plug in provider keys, rotate credentials safely, and route workloads by role and policy.',
    impact: 'Control cost, governance, and provider portability.',
  },
  {
    title: 'Operational cash-flow visibility',
    detail:
      'Tie route execution quality to margin-sensitive metrics like failed-delivery loss, exception labor, and avoidable overage in one view.',
    impact: 'Prioritize actions that protect contribution margin first.',
  },
];

const workflow: WorkflowPhase[] = [
  {
    title: 'Detect',
    detail: 'Stream incoming disruptions into a single queue with ETA confidence, risk category, and recommended owner.',
    actions: ['Live feed ingestion', 'Exception triage', 'Confidence scoring'],
  },
  {
    title: 'Decide',
    detail: 'Run route scenarios with constraints and expected cost impact before committing dispatch changes.',
    actions: ['Scenario comparison', 'Task-weighted optimization', 'Margin impact preview'],
  },
  {
    title: 'Act',
    detail: 'Execute playbooks, notify stakeholders, and track outcomes with an auditable timeline per decision.',
    actions: ['Owner handoff', 'Customer notification', 'Post-action audit trail'],
  },
];

const benchmarkSignals: BenchmarkSignal[] = [
  {
    company: 'Onfleet',
    signal: 'Publishes 400M+ deliveries and outcome benchmarks like 99% on-time and 45% fuel savings from optimized delivery operations.',
    pattern: 'Leads with quantifiable proof, then demonstrates operational modules.',
  },
  {
    company: 'project44',
    signal: 'Shows large-scale evidence: 3.7T data points annually, 700M+ daily events, and customer cost-avoidance examples such as $16M.',
    pattern: 'Pairs network scale with hard financial outcomes per use case.',
  },
  {
    company: 'FourKites',
    signal: 'Frames autonomous resolution with 85% self-resolved exceptions and a 1.1M+ partner network footprint.',
    pattern: 'Positions AI as an execution workforce, not just analytics.',
  },
  {
    company: 'Route4Me',
    signal: 'Anchors trust with 3B+ miles optimized, 30M+ routes planned, and extensive category social proof.',
    pattern: 'Uses scale metrics plus broad industry case coverage to reduce buyer risk.',
  },
  {
    company: 'FarEye',
    signal: 'Highlights enterprise outcomes including 36% growth in case narratives and measurable labor savings stories.',
    pattern: 'Combines transformation language with concrete customer wins.',
  },
];

const trustMarkers: TrustMarker[] = [
  {
    title: 'Tenant-level boundaries',
    detail: 'Company-scoped isolation across users, operations data, and provider credentials.',
  },
  {
    title: 'Encrypted key lifecycle',
    detail: 'Credential masking, secure storage, and revoke or rotate controls for incident response.',
  },
  {
    title: 'Action audit timeline',
    detail: 'Trace who changed what, when it changed, and which decision was affected.',
  },
  {
    title: 'Role-aware access',
    detail: 'Least-privilege flows for admins, dispatchers, operators, and external collaborators.',
  },
];

const plans: Plan[] = [
  {
    tier: 'starter',
    name: 'Starter',
    price: '$399/mo',
    summary: 'Single-region teams proving first route margin improvements.',
    bullets: ['Up to 25 active vehicles', '3 workspace users', '2,500 optimized tasks per month'],
    monthlyPriceUsd: 399,
  },
  {
    tier: 'scale',
    name: 'Scale',
    price: '$1,290/mo',
    summary: 'Multi-region operations that need exception playbooks and workflow automation.',
    bullets: ['Up to 250 active vehicles', '20 workspace users', '5,000 optimized tasks per month'],
    monthlyPriceUsd: 1290,
  },
  {
    tier: 'enterprise',
    name: 'Enterprise',
    price: 'Custom',
    summary: 'Global programs with governance, dedicated support, and private deployment needs.',
    bullets: ['Unlimited vehicles and regions', 'Dedicated onboarding pod', 'Private network deployment options'],
    monthlyPriceUsd: null,
  },
];

const outcomeTargets: OutcomeTarget[] = [
  {
    title: 'Exception response speed',
    baseline: 'Email-heavy, reactive triage and unclear ownership.',
    target: 'Prioritized queue with recommended owners and suggested action paths.',
    impact: 'Fewer unattended disruptions and lower SLA breach rates.',
  },
  {
    title: 'Route margin visibility',
    baseline: 'Routing, cost, and customer feedback spread across disconnected tools.',
    target: 'Single operational view across route outcomes, cost drift, and exception burden.',
    impact: 'Faster intervention on loss-making execution patterns.',
  },
  {
    title: 'Go-live readiness',
    baseline: 'Manual setup checklists with inconsistent handoffs across teams.',
    target: 'Guided desktop onboarding with explicit role milestones and launch checkpoints.',
    impact: 'Shorter time from contract to first successful dispatch cycle.',
  },
];

const launchChecklist = [
  'Create your company workspace and owner account',
  'Install desktop launch cockpit for dispatch workstations',
  'Connect provider keys and assign team roles',
  'Run dry-run route simulation and move to live operations',
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
          'Account created. Verify your email, then sign in from the desktop app or ops console to complete launch setup.',
        );
      } else {
        setStatusMessage('Company account created. Your team can now sign in from desktop and start launch readiness.');
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
    <div className="site-shell">
      <header className="top-nav reveal reveal-1">
        <a href="#top" className="brand" aria-label="FreightPilot AI home">
          <span className="brand-mark">FP</span>
          <span className="brand-text">FreightPilot AI</span>
        </a>
        <nav className="nav-links" aria-label="Primary">
          <a href="#benchmark">Benchmark</a>
          <a href="#platform">Platform</a>
          <a href="#pricing">Pricing</a>
          <a href="#roi">ROI</a>
          <a href="#signup">Signup</a>
          <a href={docsUrl} target="_blank" rel="noreferrer">
            Docs
          </a>
        </nav>
        <a className="btn btn-nav" href={appUrl} target="_blank" rel="noreferrer">
          Open Console
        </a>
      </header>

      <main id="top">
        <section className="hero-grid section-surface reveal reveal-2">
          <div className="hero-copy">
            <p className="eyebrow">Evidence-Led Logistics Orchestration</p>
            <h1>Operate with the same proof-driven rigor category leaders publish.</h1>
            <p className="lead">
              FreightPilot combines risk-aware routing, BYOK AI governance, and desktop-first launch workflows so teams can
              respond faster, protect delivery margin, and scale with confidence.
            </p>
            <div className="cta-row">
              <a className="btn btn-primary" href="#signup">
                Create company account
              </a>
              <a className="btn btn-secondary" href={downloadUrl} target="_blank" rel="noreferrer">
                Download desktop app
              </a>
            </div>
            <p className="subtle">
              Product direction benchmarked against publicly stated proof patterns from Onfleet, project44, FourKites,
              Route4Me, and FarEye.
            </p>
          </div>

          <aside className="hero-proof" aria-label="Launch readiness checklist">
            <h2>Launch readiness checklist</h2>
            <ol>
              {launchChecklist.map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ol>
            <div className="chip-row" role="list" aria-label="Core controls">
              <span role="listitem">Tenant isolation</span>
              <span role="listitem">Audit timeline</span>
              <span role="listitem">Role controls</span>
              <span role="listitem">Usage metering</span>
            </div>
          </aside>
        </section>

        <section id="benchmark" className="section">
          <div className="section-heading reveal reveal-2">
            <p className="eyebrow">Competitive Evidence</p>
            <h2>What leading logistics platforms prove publicly, and what we mirrored in this overhaul.</h2>
          </div>
          <div className="benchmark-grid">
            {benchmarkSignals.map((entry, idx) => (
              <article className={`benchmark-card reveal reveal-${idx + 2}`} key={entry.company}>
                <h3>{entry.company}</h3>
                <p>{entry.signal}</p>
                <p className="impact">Pattern adopted: {entry.pattern}</p>
              </article>
            ))}
          </div>
        </section>

        <section id="platform" className="section">
          <div className="section-heading reveal reveal-2">
            <p className="eyebrow">Platform Capabilities</p>
            <h2>Built for operators making decisions under disruption pressure.</h2>
          </div>
          <div className="capability-grid">
            {capabilities.map((feature, idx) => (
              <article className={`capability-card reveal reveal-${idx + 2}`} key={feature.title}>
                <h3>{feature.title}</h3>
                <p>{feature.detail}</p>
                <p className="impact">Impact: {feature.impact}</p>
              </article>
            ))}
          </div>
        </section>

        <section className="section process-section reveal reveal-2" aria-labelledby="process-heading">
          <div className="section-heading process-heading">
            <p className="eyebrow">Decision Loop</p>
            <h2 id="process-heading">Detect, decide, and act with one operational rhythm.</h2>
          </div>
          <div className="process-grid">
            {workflow.map((phase, idx) => (
              <article className={`process-card reveal reveal-${idx + 2}`} key={phase.title}>
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

        <section id="outcomes" className="section">
          <div className="section-heading reveal reveal-2">
            <p className="eyebrow">Outcome Playbook</p>
            <h2>Use a before-to-after model that maps directly to cash flow and service reliability.</h2>
          </div>
          <div className="outcome-grid">
            {outcomeTargets.map((item, idx) => (
              <article className={`outcome-card reveal reveal-${idx + 2}`} key={item.title}>
                <h3>{item.title}</h3>
                <p className="label">Baseline</p>
                <p>{item.baseline}</p>
                <p className="label">Target state</p>
                <p>{item.target}</p>
                <p className="impact">Impact: {item.impact}</p>
              </article>
            ))}
          </div>
        </section>

        <section id="security" className="section split-section reveal reveal-2">
          <div>
            <p className="eyebrow">Trust And Governance</p>
            <h2>Enterprise controls from day one.</h2>
            <p>
              Security and governance are built into daily workflows so operators move quickly without bypassing controls
              or introducing hidden risk.
            </p>
          </div>
          <div className="trust-grid" aria-label="Trust highlights">
            {trustMarkers.map((marker) => (
              <article className="trust-card" key={marker.title}>
                <h3>{marker.title}</h3>
                <p>{marker.detail}</p>
              </article>
            ))}
          </div>
        </section>

        <section id="pricing" className="section">
          <div className="section-heading reveal reveal-2">
            <p className="eyebrow">Pricing</p>
            <h2>Select the model that matches your operating footprint.</h2>
          </div>
          <div className="pricing-grid">
            {plans.map((plan, idx) => (
              <article
                className={`pricing-card ${tier === plan.tier ? 'selected' : ''} reveal reveal-${idx + 2}`}
                key={plan.name}
              >
                <h3>{plan.name}</h3>
                <p className="price">{plan.price}</p>
                <p>{plan.summary}</p>
                <ul>
                  {plan.bullets.map((bullet) => (
                    <li key={bullet}>{bullet}</li>
                  ))}
                </ul>
                <button
                  className="btn btn-pricing"
                  type="button"
                  onClick={() => setTier(plan.tier)}
                  aria-pressed={tier === plan.tier}
                >
                  {tier === plan.tier ? 'Selected' : `Choose ${plan.name}`}
                </button>
              </article>
            ))}
          </div>
        </section>

        <section id="roi" className="section split-section roi-section">
          <div className="reveal reveal-2">
            <p className="eyebrow">ROI Estimator</p>
            <h2>Model route and exception economics before procurement signoff.</h2>
            <p>
              Enter your current delivery profile to estimate route efficiency upside and avoidable failed-delivery loss.
              Selected plan pricing is automatically included.
            </p>
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
          <aside className="roi-panel reveal reveal-3" aria-label="ROI results">
            <p className="eyebrow">Modeled Results</p>
            <h3>{selectedPlan.name} scenario</h3>
            <ul>
              <li>
                Monthly spend baseline: <strong>${roi.monthlySpend.toLocaleString()}</strong>
              </li>
              <li>
                Route efficiency savings: <strong>${roi.optimizationSavings.toLocaleString()}</strong>
              </li>
              <li>
                Failed-delivery savings: <strong>${roi.failureSavings.toLocaleString()}</strong>
              </li>
              <li>
                Gross monthly savings: <strong>${roi.grossMonthlySavings.toLocaleString()}</strong>
              </li>
              <li>
                Platform cost: <strong>${roi.platformCost.toLocaleString()}</strong>
              </li>
              <li>
                Net monthly gain: <strong>${roi.netMonthlyGain.toLocaleString()}</strong>
              </li>
              <li>
                Annual net gain: <strong>${roi.annualNetGain.toLocaleString()}</strong>
              </li>
              <li>
                Payback window: <strong>{roi.paybackDays ? `${roi.paybackDays} days` : 'N/A for custom plan'}</strong>
              </li>
            </ul>
            <p className="subtle">
              Includes an assumed {roi.assumedFailureReductionRate}% reduction in failed-delivery incidents as a planning baseline.
            </p>
          </aside>
        </section>

        <section id="signup" className="section split-section signup-section">
          <div className="reveal reveal-2">
            <p className="eyebrow">Company Onboarding</p>
            <h2>Create your workspace and launch your desktop readiness flow.</h2>
            <p>
              Register with a company email, choose your operating tier, and move straight into the desktop launch
              cockpit to complete role assignments, connectivity checks, and go-live milestones.
            </p>
          </div>
          <form className="signup-form reveal reveal-3" onSubmit={signupAndOpenApp}>
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
              Your full name
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
              {isSubmitting ? 'Creating account...' : 'Create company account'}
            </button>
            {statusMessage ? <p className="status-note">{statusMessage}</p> : null}
          </form>
        </section>

        <section className="final-cta reveal reveal-3">
          <h2>Move from visibility to decisive execution.</h2>
          <p>
            FreightPilot is built for teams that want provable operational outcomes, not another dashboard that reports
            problems after the margin is gone.
          </p>
          <div className="cta-row">
            <a className="btn btn-primary" href="#signup">
              Start company setup
            </a>
            <a className="btn btn-secondary" href={docsUrl} target="_blank" rel="noreferrer">
              Review implementation docs
            </a>
          </div>
        </section>
      </main>
    </div>
  );
}

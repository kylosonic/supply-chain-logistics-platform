import { FormEvent, useMemo, useState } from 'react';

import { companySignup, type SignupTier } from './services';

type Feature = {
  title: string;
  detail: string;
  impact: string;
};

type Plan = {
  tier: SignupTier;
  name: string;
  price: string;
  summary: string;
  bulletA: string;
  bulletB: string;
  bulletC: string;
  monthlyPriceUsd: number | null;
};

type OutcomeTarget = {
  title: string;
  baseline: string;
  target: string;
  impact: string;
};

const features: Feature[] = [
  {
    title: 'Risk-aware route optimization',
    detail:
      'Blend live weather, geopolitical disruption, and regional congestion signals to assign safer and faster truck routes.',
    impact: 'Reduce late deliveries during disruptions',
  },
  {
    title: 'Bring your own AI provider',
    detail:
      'Each company can plug in its own model provider and API keys for forecasting and route intelligence.',
    impact: 'Keep model strategy under your control',
  },
  {
    title: 'Control tower dashboards',
    detail:
      'Track fleet performance, inventory health, and exception alerts from one desktop-first operations workspace.',
    impact: 'Shorten decision cycles for dispatch teams',
  },
];

const plans: Plan[] = [
  {
    tier: 'starter',
    name: 'Starter',
    price: '$399/mo',
    summary: 'For small regional fleets and single dispatch teams.',
    bulletA: 'Up to 25 active vehicles',
    bulletB: '3 workspace users',
    bulletC: '2,500 optimized tasks per month, then usage-based overage',
    monthlyPriceUsd: 399,
  },
  {
    tier: 'scale',
    name: 'Scale',
    price: '$1,290/mo',
    summary: 'For multi-region logistics operations with live risk feeds.',
    bulletA: 'Up to 250 active vehicles',
    bulletB: '20 workspace users',
    bulletC: '5,000 optimized tasks per month with workflow automations',
    monthlyPriceUsd: 1290,
  },
  {
    tier: 'enterprise',
    name: 'Enterprise',
    price: 'Custom',
    summary: 'For global networks with governance and dedicated infrastructure.',
    bulletA: 'Unlimited vehicles and regions',
    bulletB: 'Dedicated onboarding pod',
    bulletC: 'Private network deployment options',
    monthlyPriceUsd: null,
  },
];

const outcomeTargets: OutcomeTarget[] = [
  {
    title: 'Exception response speed',
    baseline: 'Reactive email and spreadsheet triage',
    target: 'Control tower alerts with guided owner actions',
    impact: 'Reduce SLA misses from unresolved disruptions',
  },
  {
    title: 'Route margin visibility',
    baseline: 'Cost and ETA tracked in separate systems',
    target: 'Dispatch, route cost, and alert data in one workspace',
    impact: 'See profitable vs loss-making routes earlier',
  },
  {
    title: 'Onboarding cycle time',
    baseline: 'Manual setup across multiple tools',
    target: 'Company signup, desktop setup, and team launch workflow',
    impact: 'Get new operations teams active faster',
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
          'Account created. Check your email to verify your account, then sign in from the desktop app or ops console.',
        );
      } else {
        setStatusMessage('Company account created. You can now sign in from the desktop app or ops console.');
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
          <a href="#features">Platform</a>
          <a href="#outcomes">Outcomes</a>
          <a href="#pricing">Pricing</a>
          <a href="#roi">ROI</a>
          <a href="#security">Security</a>
          <a href={docsUrl} target="_blank" rel="noreferrer">
            Docs
          </a>
        </nav>
        <a className="btn btn-quiet" href={appUrl} target="_blank" rel="noreferrer">
          Open Console
        </a>
      </header>

      <main id="top">
        <section className="hero-grid">
          <div className="hero-copy reveal reveal-2">
            <p className="eyebrow">Desktop Logistics Intelligence Platform</p>
            <h1>Optimize routes with your own AI keys, not someone else&apos;s black box.</h1>
            <p className="lead">
              FreightPilot AI gives every logistics company a secure control tower: sign up, invite your team, connect
              your provider keys, and dispatch smarter routes based on weather and real-time disruption signals.
            </p>
            <div className="cta-row">
              <a className="btn btn-primary" href="#signup">
                Create company account
              </a>
              <a className="btn btn-secondary" href={downloadUrl} target="_blank" rel="noreferrer">
                Download desktop app
              </a>
            </div>
            <p className="subtle">Supports bring-your-own-key workflows for OpenAI-compatible providers and private endpoints.</p>
          </div>

          <aside className="hero-panel reveal reveal-3" aria-label="Launch checklist">
            <h2>Launch in 4 steps</h2>
            <ol>
              <li>Create your company workspace</li>
              <li>Install desktop on dispatch machines</li>
              <li>Add provider API keys in the admin portal</li>
              <li>Run risk-aware optimization with live constraints</li>
            </ol>
            <div className="pill-row" role="list" aria-label="Platform highlights">
              <span role="listitem">Tenant isolation</span>
              <span role="listitem">Audit logs</span>
              <span role="listitem">Role-based access</span>
            </div>
          </aside>
        </section>

        <section id="features" className="section">
          <div className="section-heading reveal reveal-2">
            <p className="eyebrow">What Teams Get</p>
            <h2>Built for operators who plan under pressure.</h2>
          </div>
          <div className="card-grid">
            {features.map((feature, idx) => (
              <article className={`feature-card reveal reveal-${idx + 2}`} key={feature.title}>
                <h3>{feature.title}</h3>
                <p>{feature.detail}</p>
                <p className="impact">Impact: {feature.impact}</p>
              </article>
            ))}
          </div>
        </section>

        <section id="outcomes" className="section">
          <div className="section-heading reveal reveal-2">
            <p className="eyebrow">Outcome Playbook</p>
            <h2>Measure value in margin, speed, and reliability.</h2>
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

        <section id="security" className="section split-section">
          <div className="reveal reveal-2">
            <p className="eyebrow">Security</p>
            <h2>Enterprise controls from day one.</h2>
            <p>
              Keep customer operations data separated by tenant, store provider credentials with encryption at rest,
              and enforce least-privilege access with role-aware permissions.
            </p>
          </div>
          <ul className="security-list reveal reveal-3" aria-label="Security highlights">
            <li>Company-scoped data partitioning and user boundaries</li>
            <li>Encrypted API key storage with masked visibility</li>
            <li>Action-level audit timeline for admin and dispatcher actions</li>
            <li>Environment-based key rotation and emergency revoke options</li>
          </ul>
        </section>

        <section id="pricing" className="section">
          <div className="section-heading reveal reveal-2">
            <p className="eyebrow">Pricing</p>
            <h2>Choose the operating model that fits your fleet.</h2>
          </div>
          <div className="pricing-grid">
            {plans.map((plan, idx) => (
              <article className={`pricing-card reveal reveal-${idx + 2}`} key={plan.name}>
                <h3>{plan.name}</h3>
                <p className="price">{plan.price}</p>
                <p>{plan.summary}</p>
                <ul>
                  <li>{plan.bulletA}</li>
                  <li>{plan.bulletB}</li>
                  <li>{plan.bulletC}</li>
                </ul>
                <a className="btn btn-quiet" href="#signup">
                  Choose {plan.name}
                </a>
              </article>
            ))}
          </div>
        </section>

        <section id="roi" className="section split-section roi-grid">
          <div className="reveal reveal-2">
            <p className="eyebrow">ROI Estimator</p>
            <h2>Model your monthly and annual operating upside.</h2>
            <p>
              Use your delivery volume and cost baseline to estimate savings from route optimization and exception
              automation. The model applies your selected subscription tier as the platform cost.
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
            <h3>{selectedPlan.name} plan scenario</h3>
            <ul>
              <li>
                Monthly delivery spend baseline: <strong>${roi.monthlySpend.toLocaleString()}</strong>
              </li>
              <li>
                Route efficiency savings: <strong>${roi.optimizationSavings.toLocaleString()}</strong>
              </li>
              <li>
                Failed delivery reduction savings: <strong>${roi.failureSavings.toLocaleString()}</strong>
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
              This estimator is a planning tool. Use your own costs and delivery profile to refine commercial forecasts.
            </p>
          </aside>
        </section>

        <section id="signup" className="section split-section">
          <div className="reveal reveal-2">
            <p className="eyebrow">Company Onboarding</p>
            <h2>Create your company account</h2>
            <p>
              Use a company email, choose a subscription tier, and your team can immediately log in from the desktop
              app and manage provider API keys.
            </p>
          </div>
          <form className="security-list reveal reveal-3" onSubmit={signupAndOpenApp}>
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
              {isSubmitting ? 'Creating account…' : 'Create company account'}
            </button>
            {statusMessage ? <p>{statusMessage}</p> : null}
          </form>
        </section>

        <section className="final-cta reveal reveal-3">
          <h2>Start with your own keys. Keep your own control.</h2>
          <p>
            FreightPilot AI is designed so you can modernize routing intelligence without replacing your security model
            or vendor strategy.
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

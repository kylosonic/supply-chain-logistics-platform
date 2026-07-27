import { FormEvent, useState } from 'react';

import { companySignup, type SignupTier } from './services';

type Feature = {
  title: string;
  detail: string;
  impact: string;
};

type Plan = {
  name: string;
  price: string;
  summary: string;
  bulletA: string;
  bulletB: string;
  bulletC: string;
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
    name: 'Starter',
    price: '$399/mo',
    summary: 'For small regional fleets and single dispatch teams.',
    bulletA: 'Up to 25 active vehicles',
    bulletB: '3 workspace users',
    bulletC: 'BYOK AI integration',
  },
  {
    name: 'Scale',
    price: '$1,290/mo',
    summary: 'For multi-region logistics operations with live risk feeds.',
    bulletA: 'Up to 250 active vehicles',
    bulletB: '20 workspace users',
    bulletC: 'Priority support and SSO',
  },
  {
    name: 'Enterprise',
    price: 'Custom',
    summary: 'For global networks with governance and dedicated infrastructure.',
    bulletA: 'Unlimited vehicles and regions',
    bulletB: 'Dedicated onboarding pod',
    bulletC: 'Private network deployment options',
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
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [statusMessage, setStatusMessage] = useState<string | null>(null);

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
          <a href="#pricing">Pricing</a>
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

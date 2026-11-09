import {
  ArrowUpRight,
  BadgeCheck,
  Boxes,
  Cable,
  Cpu,
  type LucideIcon,
  Layers3,
  Orbit,
  Radar,
  ShieldCheck,
  TimerReset,
  Workflow,
} from 'lucide-react';

export type NavItem = {
  label: string;
  href: string;
  description: string;
};

export type FeatureCard = {
  icon: LucideIcon;
  title: string;
  description: string;
  detail: string;
};

export type TimelineItem = {
  title: string;
  detail: string;
  label: string;
};

export type PricingTier = {
  name: string;
  price_etb: number;
  billing_cycle: 'per month' | 'per quarter';
  included_units: {
    delivery_tasks: number | null;
    route_optimizations: number | null;
  };
  overage_rates: {
    delivery_tasks: number | null;
    route_optimizations: number | null;
  };
  summary: string;
};

export type FaqItem = {
  question: string;
  answer: string;
};

// Locked copy (blueprint §5 — [EXACT] strings, byte-identical)

export const heroHeadline = 'Run your first optimized route in 5 minutes. Free.';

export const heroParagraph =
  'Sign up and your workspace loads with sample data — warehouses, fleet, inventory, orders, all ready. Optimize your first route immediately. Upload your real CSVs when you\'re ready. Pay by bank transfer to CBE or Dashen when you outgrow the free tier. No card, no commitment.';

export const startFreeCta = 'Start free';

export const howItWorksHeading = 'How it works in 5 minutes';
export const showLabel = 'Show';
export const hideLabel = 'Hide';

export const howItWorksSteps = [
  'Sign up free — your workspace loads with sample data in under a minute.',
  'Run your first route optimization on the sample data — see the map, the stops, the schedule.',
  'Upload your real CSVs (warehouses, items, fleet, inventory, orders) when you\'re ready. Pay by bank transfer to CBE or Dashen when you outgrow the free tier.',
] as const;

export const pricingTiers: PricingTier[] = [
  {
    name: 'Starter',
    price_etb: 4500,
    billing_cycle: 'per month',
    included_units: { delivery_tasks: 2500, route_optimizations: 50 },
    overage_rates: { delivery_tasks: 0.2, route_optimizations: 1.5 },
    summary: 'First lift off Free tier',
  },
  {
    name: 'Scale',
    price_etb: 10000,
    billing_cycle: 'per quarter',
    included_units: { delivery_tasks: 5000, route_optimizations: 250 },
    overage_rates: { delivery_tasks: 0.16, route_optimizations: 1.0 },
    summary: 'Mid-size dispatch shop',
  },
  {
    name: 'Enterprise',
    price_etb: 45000,
    billing_cycle: 'per quarter',
    included_units: { delivery_tasks: null, route_optimizations: null },
    overage_rates: { delivery_tasks: null, route_optimizations: null },
    summary: 'Unlimited usage, dedicated support',
  },
];

export const freeLine = 'Free forever — 2,500 delivery tasks / month, no payment ever. Start here.';

export const partialPaymentStory =
  'Partial payments welcome. Pay what your cash flow allows — send the receipt for each transfer, and your workspace unlocks when the full balance clears. If you overpay within 1,000 ETB, the surplus applies as credit to your next invoice.';

export const paymentPaceStory =
  'Pay at your bank\'s pace — your first invoice isn\'t due until the start of the next billing period.';

export const trustStripLine =
  'Bank transfer to CBE or Dashen. No card required. Partial payments welcome. No hidden fees, no annual lock-in.';

export const verificationLine = 'Bank transfer to CBE or Dashen — receipt verified within 24 hours.';

export const signupFormSubline = 'Start free, no card required.';

export const signupFormNote = 'No card required. Your workspace loads with sample data.';

export const signupSuccessMessage = 'Workspace created — sample data loaded.';

export const networkFailureMessage =
  'Could not create the company workspace. Check your connection and try again.';

export const afterSignupSteps = [
  {
    label: '01',
    title: 'Your workspace loads with sample data',
    detail: 'Warehouses, fleet, inventory, and orders are all ready. No uploads needed to start.',
  },
  {
    label: '02',
    title: 'Run your first route optimization',
    detail: 'See the map, the stops, and the schedule on the sample data.',
  },
  {
    label: '03',
    title: "Upload your real CSVs when you're ready",
    detail: 'Pay by bank transfer to CBE or Dashen when you outgrow the free tier.',
  },
];

export const faqItems: FaqItem[] = [
  {
    question: 'Do you offer a free trial?',
    answer:
      'The Free tier is free forever — 2,500 delivery tasks per month, no payment ever. When you upgrade to a paid tier from inside your workspace, the first 7 days on that tier are a trial at no charge.',
  },
  {
    question: 'What does the Starter tier include?',
    answer:
      'Starter costs 4,500 ETB per month. It includes 2,500 delivery tasks and 50 route optimizations. Extra delivery tasks cost 0.20 ETB each, and extra route optimizations cost 1.50 ETB each.',
  },
  {
    question: 'What does the Scale tier include?',
    answer:
      'Scale costs 10,000 ETB per quarter. It includes 5,000 delivery tasks and 250 route optimizations. Extra delivery tasks cost 0.16 ETB each, and extra route optimizations cost 1.00 ETB each.',
  },
  {
    question: 'What does the Enterprise tier include?',
    answer:
      'Enterprise costs 45,000 ETB per quarter with unlimited usage and no overage rates. It includes dedicated support.',
  },
  {
    question: 'How do payments work?',
    answer:
      'Pay by bank transfer to CBE or Dashen — receipt verified within 24 hours. Partial payments are welcome: pay what your cash flow allows, send the receipt for each transfer, and your workspace unlocks when the full balance clears. If you overpay within 1,000 ETB, the surplus applies as credit to your next invoice.',
  },
];

// Site structure

export const externalLinks = {
  console: process.env.NEXT_PUBLIC_APP_CONSOLE_URL || 'https://ops-console-azure.vercel.app',
  docs: '/docs',
  desktop: process.env.NEXT_PUBLIC_DESKTOP_DOWNLOAD_URL || 'https://example.com/download',
};

export const navigation: NavItem[] = [
  { label: 'Home', href: '/', description: 'Product overview' },
  { label: 'Platform', href: '/platform', description: 'Operational modules' },
  { label: 'Technology', href: '/technology', description: 'Decision controls' },
  { label: 'Pricing', href: '/pricing', description: 'Commercial plans' },
  { label: 'Launch', href: '/launch', description: 'Workspace setup' },
  { label: 'Contact', href: '/contact', description: 'Get in touch' },
];

/**
 * Footer link data — dead links removed for v1 (blueprint §1.12): no
 * `/privacy`, `/terms`, `/security` routes exist, and About/Blog/Careers/
 * Community pointed at `#`.
 */
export const footerNavigation = {
  platform: [
    { label: 'Control Tower', href: '/platform#control-tower' },
    { label: 'Decision Studio', href: '/platform#decision-studio' },
    { label: 'Launch Workstation', href: '/platform#launch-workstation' },
    { label: 'Revenue Guard', href: '/platform#revenue-guard' },
  ],
  resources: [
    { label: 'Documentation', href: externalLinks.docs },
    { label: 'API Reference', href: '/docs#api' },
    { label: 'Open console', href: externalLinks.console },
  ],
  company: [
    { label: 'Contact', href: '/contact' },
    { label: 'Privacy', href: '/privacy' },
    { label: 'Terms', href: '/terms' },
    { label: 'Security', href: '/security' },
    { label: 'Status', href: '/status' },
  ],
};

export const platformStacks: FeatureCard[] = [
  {
    icon: Layers3,
    title: 'Control Tower',
    description: 'One workspace for routes, alerts, shipments, planning, and governance.',
    detail: 'Keep the operator in one system instead of splitting planning and response across separate tools.',
  },
  {
    icon: Workflow,
    title: 'Decision Studio',
    description: 'Compare route tradeoffs with time, cost, and execution impact still visible.',
    detail: 'Scenario work stays close to live operations instead of becoming a disconnected planning exercise.',
  },
  {
    icon: Orbit,
    title: 'Launch Workstation',
    description: 'Run onboarding as a controlled rollout with explicit milestones and owners.',
    detail: 'Keep operators, data owners, and security leads aligned before the first live production window.',
  },
  {
    icon: TimerReset,
    title: 'Revenue Guard',
    description: 'Review task usage, service failures, and platform limits during daily operations.',
    detail: 'Commercial visibility is built into the workflow instead of treated as a separate reporting task.',
  },
];

export const operatingLoop: TimelineItem[] = [
  {
    label: '01',
    title: 'Surface issues before they spread',
    detail: 'Watch live exceptions, shipment drift, and stock pressure while there is still time to respond cleanly.',
  },
  {
    label: '02',
    title: 'Make decisions with the full picture in view',
    detail: 'Route options, workload, approvals, and workspace posture stay visible while the team decides what to do next.',
  },
  {
    label: '03',
    title: 'Record actions and handoffs clearly',
    detail: 'Every important workspace action can be reviewed through audit history and route scenario records.',
  },
];

export const technologyLayers: FeatureCard[] = [
  {
    icon: Radar,
    title: 'Operational signal layer',
    description: 'Live feeds, routing constraints, inventory posture, and workspace usage are captured together.',
    detail: 'Decision quality improves when the product works from shared operational signal instead of isolated screens.',
  },
  {
    icon: Cpu,
    title: 'AI provider controls',
    description: 'Provider choice, model routing, and automation settings remain visible to the workspace owner.',
    detail: 'The system can assist decisions without turning approvals and provider behavior into a black box.',
  },
  {
    icon: ShieldCheck,
    title: 'Governance by default',
    description: 'Workspace changes, provider actions, and route decisions are recorded and reviewable.',
    detail: 'The platform is designed to support accountable operations, not just fast interaction.',
  },
  {
    icon: Cable,
    title: 'Coordinated rollout',
    description: 'Desktop, web, and operator surfaces are built to support one launch process.',
    detail: 'Each layer reinforces the rollout workflow instead of forcing the team to improvise one.',
  },
];

export const codeSnippet = `const decision = await freightPilot.route.plan({
  lane: "WH-A -> WEST-HUB",
  objective: "margin_protection",
  inputs: ["inventory", "shipments", "exceptions", "usage"],
  aiProvider: workspace.preferredProvider,
});

if (decision.unassignedCount > 0) {
  await ops.exceptionFeed.raise({
    severity: "high",
    reason: "capacity constraint",
  });
}`;

/** Honest trust signals — each one maps to a verifiable product behavior. */
export const trustSignals = [
  'Bank transfer to CBE or Dashen',
  'No card required',
  'Sample data on signup',
  'Partial payments welcome',
  'Audit timelines',
  'Usage metering',
];

export const iconLinks = [
  { label: 'Open console', href: externalLinks.console, icon: ArrowUpRight },
  { label: 'Download desktop', href: externalLinks.desktop, icon: Boxes },
  { label: 'Read docs', href: externalLinks.docs, icon: BadgeCheck },
];

export const trustRibbon = ['Audit key changes', 'Control provider access', 'Roll out teams in stages'];

import {
  Activity,
  ArrowUpRight,
  BadgeCheck,
  BrainCircuit,
  Boxes,
  Cable,
  Command,
  Compass,
  Cpu,
  Fingerprint,
  Gauge,
  Glasses,
  Layers3,
  type LucideIcon,
  Orbit,
  Radar,
  Route,
  ShieldCheck,
  Sparkles,
  TimerReset,
  Waypoints,
  Workflow,
  Zap,
} from 'lucide-react';

export type NavItem = {
  label: string;
  href: string;
  description: string;
};

export type StatItem = {
  value: number;
  suffix?: string;
  label: string;
  detail: string;
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
  price: string;
  eyebrow: string;
  summary: string;
  bullets: string[];
  cta: string;
};

export type Testimonial = {
  company: string;
  quote: string;
  person: string;
  role: string;
  avatarColor: string;
};

export type FaqItem = {
  question: string;
  answer: string;
};

export const externalLinks = {
  console: process.env.NEXT_PUBLIC_APP_CONSOLE_URL || 'http://localhost',
  docs: process.env.NEXT_PUBLIC_DOCS_URL || 'https://example.com/docs',
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

export const footerNavigation = {
  platform: [
    { label: 'Control Tower', href: '/platform#control-tower' },
    { label: 'Decision Studio', href: '/platform#decision-studio' },
    { label: 'Launch Workstation', href: '/platform#launch-workstation' },
    { label: 'Revenue Guard', href: '/platform#revenue-guard' },
  ],
  resources: [
    { label: 'Documentation', href: externalLinks.docs },
    { label: 'API Reference', href: externalLinks.docs + '/api' },
    { label: 'Desktop App', href: externalLinks.desktop },
    { label: 'Community', href: '#' },
  ],
  company: [
    { label: 'About', href: '#' },
    { label: 'Blog', href: '#' },
    { label: 'Careers', href: '#' },
    { label: 'Contact', href: '/contact' },
  ],
  legal: [
    { label: 'Privacy Policy', href: '/privacy' },
    { label: 'Terms of Service', href: '/terms' },
    { label: 'Security', href: '/security' },
  ],
};

export const homeStats: StatItem[] = [
  {
    value: 48,
    suffix: 'hrs',
    label: 'Faster pilot activation',
    detail: 'Move from workspace creation to a controlled launch window in two days instead of weeks.',
  },
  {
    value: 87,
    suffix: '%',
    label: 'Decisions with context',
    detail: 'Route health, workload, launch readiness, and provider settings stay visible in the same workflow.',
  },
  {
    value: 5,
    suffix: 'x',
    label: 'Less interface switching',
    detail: 'Give operators one place to review exceptions, compare actions, and record decisions.',
  },
  {
    value: 1,
    suffix: ' unified workflow',
    label: 'Shared operating model',
    detail: 'Plan, respond, approve, and audit work inside a single connected control layer.',
  },
];

export const flagshipFeatures: FeatureCard[] = [
  {
    icon: Route,
    title: 'Route planning with live exceptions',
    description: 'Plan routes and react to service issues from the same operational view.',
    detail: 'Keep late shipments, capacity risks, and route changes visible while a dispatcher is deciding what to do next.',
  },
  {
    icon: BrainCircuit,
    title: 'AI assistance with visible controls',
    description: 'Support decisions with models without hiding who approved what or which provider was used.',
    detail: 'Provider selection, workspace policy, and action history remain part of the operating record.',
  },
  {
    icon: Gauge,
    title: 'Operational and commercial visibility',
    description: 'Review service risk, workload pressure, and usage posture together.',
    detail: 'The product keeps execution quality and platform usage in the same decision context.',
  },
  {
    icon: Command,
    title: 'Launch workflows for real teams',
    description: 'Prepare devices, users, and integrations before the first production shift.',
    detail: 'Track connection health, role sign-off, and launch readiness with a dedicated workstation flow.',
  },
];

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

export const testimonials: Testimonial[] = [
  {
    company: 'Northstar Distribution',
    quote:
      'FreightPilot gives the dispatch team one place to review route risk, operator readiness, and workspace controls without hunting across multiple screens.',
    person: 'Amina K.',
    role: 'VP Operations',
    avatarColor: 'from-cyan-400 to-blue-500',
  },
  {
    company: 'Contour Fulfillment',
    quote:
      'It keeps planning, exceptions, and approvals close enough together that supervisors can respond quickly without losing context.',
    person: 'Julian R.',
    role: 'Head of Logistics Systems',
    avatarColor: 'from-violet-400 to-purple-500',
  },
  {
    company: 'Helix Commerce Network',
    quote:
      'The launch workflow is practical. We can track sign-off, environment checks, and rollout readiness before opening a new team to live work.',
    person: 'Marta S.',
    role: 'Program Director',
    avatarColor: 'from-amber-400 to-orange-500',
  },
];

export const pricingTiers: PricingTier[] = [
  {
    name: 'Starter',
    price: '$399/mo',
    eyebrow: 'For a single region or pilot team',
    summary: 'Cover core routing, exception review, and workspace launch for an initial operating footprint.',
    bullets: ['25 active vehicles', '3 workspace users', '2,500 optimized tasks', 'Desktop launch workstation'],
    cta: 'Choose Starter',
  },
  {
    name: 'Scale',
    price: '$1,290/mo',
    eyebrow: 'For growing multi-site operations',
    summary: 'Add more users, more vehicles, and tighter operational controls across a broader routing network.',
    bullets: ['250 active vehicles', '20 workspace users', '5,000 optimized tasks', 'Priority rollout guidance'],
    cta: 'Choose Scale',
  },
  {
    name: 'Enterprise',
    price: 'Custom',
    eyebrow: 'For enterprise rollout programs',
    summary: 'Add tailored rollout planning, advanced controls, and deployment options for larger operating environments.',
    bullets: ['Unlimited regions', 'Dedicated onboarding pod', 'Custom rollout controls', 'Private deployment patterns'],
    cta: 'Talk to sales',
  },
];

export const faqItems: FaqItem[] = [
  {
    question: 'Is this a route tool, a control tower, or an AI product?',
    answer:
      'It brings those functions together. FreightPilot combines route planning, live issue handling, launch readiness, and provider controls in one operational workspace.',
  },
  {
    question: 'Can we keep our own provider strategy?',
    answer:
      'Yes. Teams can manage provider keys, select preferred providers, and keep a bring-your-own-key model instead of being forced into a single vendor.',
  },
  {
    question: 'What is different about the desktop experience?',
    answer:
      'The desktop layer supports rollout work directly. It is designed for workstation readiness, controlled sign-off, and operator-specific launch tasks.',
  },
  {
    question: 'How does FreightPilot justify premium positioning?',
    answer:
      'The product is positioned around operational clarity, controlled rollout, and accountable decision support rather than visual styling alone.',
  },
  {
    question: 'Does the site reflect real product capability?',
    answer:
      'Yes. The website is structured around routing, alerting, launch, usage, and governance workflows that already exist in the product.',
  },
];

export const launchSteps: TimelineItem[] = [
  {
    label: '01',
    title: 'Create the company workspace',
    detail: 'Provision the owner account, choose the operating tier, and assign rollout ownership.',
  },
  {
    label: '02',
    title: 'Prepare the launch workstation',
    detail: 'Give operators a desktop entry point that validates device and environment setup before first use.',
  },
  {
    label: '03',
    title: 'Connect data, providers, and users',
    detail: 'Load warehouses, items, fleet, inventory, and orders while assigning roles and provider settings.',
  },
  {
    label: '04',
    title: 'Run the first live window',
    detail: 'Move through dry-run routing, readiness checks, and a controlled production launch.',
  },
];

export const trustSignals = [
  'Workspace tenancy',
  'Provider-key masking',
  'Audit timelines',
  'Usage metering',
  'Role-aware launch sign-off',
  'Scenario history',
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

export const premiumBadges = ['Route planning', 'Exception monitoring', 'Workspace launch', 'Provider controls'];

export const deepLinks = {
  docs: externalLinks.docs,
  console: externalLinks.console,
  desktop: externalLinks.desktop,
};

export const secondaryFeatures: FeatureCard[] = [
  {
    icon: Sparkles,
    title: 'Clear operator context',
    description: 'Pages are structured so important actions and signals can be found quickly.',
    detail: 'Spacing, contrast, and hierarchy are used to support reading speed and decision quality.',
  },
  {
    icon: Glasses,
    title: 'Reduced interface noise',
    description: 'Visual treatment is present, but it does not compete with the information itself.',
    detail: 'The site keeps enough atmosphere to feel modern without pushing content into the background.',
  },
  {
    icon: Waypoints,
    title: 'Structured rollout steps',
    description: 'The launch flow makes responsibilities and milestones explicit from the start.',
    detail: 'Teams can see what is complete, what is blocked, and what still needs review.',
  },
  {
    icon: Fingerprint,
    title: 'Provider and policy controls',
    description: 'Governance settings are treated as operational controls instead of buried configuration.',
    detail: 'The product makes it easier to manage provider access and review changes as the team scales.',
  },
];

export const pageIntro = {
  home: {
    eyebrow: 'FreightPilot platform',
    title: 'Plan routes, manage exceptions, and launch operations from one control layer.',
    description:
      'A multi-page product site that explains the same routing, launch, and governance workflows available in the product itself.',
  },
};

export const iconLinks = [
  { label: 'Open console', href: externalLinks.console, icon: ArrowUpRight },
  { label: 'Download desktop', href: externalLinks.desktop, icon: Boxes },
  { label: 'Read docs', href: externalLinks.docs, icon: BadgeCheck },
];

export const benefitStrip = [
  'Route planning and dispatch review',
  'Exception monitoring and handoff',
  'Provider controls and audit history',
  'Workspace launch and readiness checks',
];

export const trustRibbon = ['Audit key changes', 'Control provider access', 'Roll out teams in stages'];

export const platformNarrative = [
  'FreightPilot keeps planning, exception response, and workspace governance in one product model.',
  'The site is organized around real operator tasks instead of generic category messaging.',
  'Each page explains a different workflow while keeping the information hierarchy consistent.',
];

export const pageCards: FeatureCard[] = [
  {
    icon: Compass,
    title: 'Home',
    description: 'A concise overview of planning, exceptions, rollout, and provider controls.',
    detail: 'Use this page to understand the product scope and move into the relevant workflow.',
  },
  {
    icon: Layers3,
    title: 'Platform',
    description: 'A page focused on product modules, workflows, and operational responsibilities.',
    detail: 'Use this page to understand how the product is organized for day-to-day work.',
  },
  {
    icon: Activity,
    title: 'Technology',
    description: 'A page centered on providers, governance, and decision support controls.',
    detail: 'Use this page when teams need to understand how model use is controlled and reviewed.',
  },
  {
    icon: Zap,
    title: 'Pricing + Launch',
    description: 'Commercial planning and workspace setup guidance for real rollout work.',
    detail: 'Use these pages to move from evaluation into a controlled pilot or launch.',
  },
];
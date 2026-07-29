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
  { label: 'Home', href: '/', description: 'Launch narrative' },
  { label: 'Platform', href: '/platform', description: 'Command stack' },
  { label: 'Technology', href: '/technology', description: 'AI systems' },
  { label: 'Pricing', href: '/pricing', description: 'Commercial model' },
  { label: 'Launch', href: '/launch', description: 'Workspace onboarding' },
];

export const homeStats: StatItem[] = [
  {
    value: 48,
    suffix: 'hrs',
    label: 'Faster pilot activation',
    detail: 'Reduce the time between workspace creation and the first controlled dispatch window.',
  },
  {
    value: 87,
    suffix: '%',
    label: 'Higher decision visibility',
    detail: 'Routes, exceptions, pricing pressure, and launch readiness sit in one command narrative.',
  },
  {
    value: 5,
    suffix: 'x',
    label: 'Cleaner operator context',
    detail: 'Design every interaction to remove noise and make escalation paths obvious.',
  },
  {
    value: 1,
    suffix: 'loop',
    label: 'Unified operating rhythm',
    detail: 'Detect, decide, act, and govern without changing mental models between tools.',
  },
];

export const flagshipFeatures: FeatureCard[] = [
  {
    icon: Route,
    title: 'Exception-led route command',
    description: 'A surface for teams who dispatch under consequence, not just plan routes on a map.',
    detail: 'Surface route drift, shipment risk, cost variance, and operator action in the same visual field.',
  },
  {
    icon: BrainCircuit,
    title: 'AI orchestration without black boxes',
    description: 'Bring-your-own models, provider governance, and decision explainability built into the product story.',
    detail: 'Use provider preferences, workspace controls, and action traces as part of normal operations.',
  },
  {
    icon: Gauge,
    title: 'Margin-aware execution',
    description: 'Focus attention on the flows that are actually expensive, not just the flows that are noisy.',
    detail: 'Tie overage, failed-delivery loss, replenishment risk, and route execution quality together.',
  },
  {
    icon: Command,
    title: 'Desktop launch readiness',
    description: 'Make rollout feel like an operating ritual, not a buried implementation checklist.',
    detail: 'Connection health, role sign-off, and live-go readiness live in a dedicated workstation flow.',
  },
];

export const platformStacks: FeatureCard[] = [
  {
    icon: Layers3,
    title: 'Control Tower',
    description: 'One visual layer for routes, alerts, shipments, planning, and workspace governance.',
    detail: 'Give operators a central rhythm instead of forcing them to build one from disconnected screens.',
  },
  {
    icon: Workflow,
    title: 'Decision Studio',
    description: 'Model routing tradeoffs with time, cost, and launch readiness still visible.',
    detail: 'Treat scenario work as a live operating decision, not a background planning artifact.',
  },
  {
    icon: Orbit,
    title: 'Launch Workstation',
    description: 'Turn onboarding into a controlled launch sequence with explicit milestones.',
    detail: 'Keep operators, data owners, and security leads aligned before the first production window.',
  },
  {
    icon: TimerReset,
    title: 'Revenue Guard',
    description: 'Keep task usage, service failure, and cost pressure in the room while decisions are being made.',
    detail: 'A commercial layer that feels operational instead of feeling bolted onto the product.',
  },
];

export const operatingLoop: TimelineItem[] = [
  {
    label: '01',
    title: 'Detect risk before the customer feels it',
    detail: 'Use live exception queues, shipment drift, and stock pressure to see the next problem while it is still small.',
  },
  {
    label: '02',
    title: 'Decide with context still intact',
    detail: 'Routes, approvals, commercial posture, and launch readiness all stay present during decision moments.',
  },
  {
    label: '03',
    title: 'Act with a recorded chain of intent',
    detail: 'Every important workspace move becomes reviewable through audit events and route scenario history.',
  },
];

export const technologyLayers: FeatureCard[] = [
  {
    icon: Radar,
    title: 'Signal ingestion',
    description: 'Live feeds, routing constraints, inventory posture, and workspace usage feed the same product brain.',
    detail: 'Build decision quality from layered operational signal, not isolated screen state.',
  },
  {
    icon: Cpu,
    title: 'AI coordination',
    description: 'Provider choice, model routing, and automation framing are treated as operator-visible controls.',
    detail: 'The system feels intelligent without asking the team to trust a hidden chain of decisions.',
  },
  {
    icon: ShieldCheck,
    title: 'Governance by default',
    description: 'Workspace preference changes, provider actions, and route decisions are auditable.',
    detail: 'Premium software should feel accountable as well as cinematic.',
  },
  {
    icon: Cable,
    title: 'Composable deployment',
    description: 'Desktop, product site, and operator console are presented as one orchestrated system.',
    detail: 'Every layer supports the launch experience rather than fighting it.',
  },
];

export const testimonials: Testimonial[] = [
  {
    company: 'Northstar Distribution',
    quote:
      'FreightPilot feels like the first control layer that understands dispatch urgency, finance pressure, and rollout discipline at the same time.',
    person: 'Amina K.',
    role: 'VP Operations',
  },
  {
    company: 'Contour Fulfillment',
    quote:
      'The product doesn’t just visualize problems. It changes how the team sequences decisions when the day stops being predictable.',
    person: 'Julian R.',
    role: 'Head of Logistics Systems',
  },
  {
    company: 'Helix Commerce Network',
    quote:
      'The launch workstation alone changed the way we roll out new operator machines. It turned implementation into an actual operating practice.',
    person: 'Marta S.',
    role: 'Program Director',
  },
];

export const pricingTiers: PricingTier[] = [
  {
    name: 'Starter',
    price: '$399/mo',
    eyebrow: 'For emerging regional teams',
    summary: 'Replace reactive dispatch habits with a premium control layer for one core region.',
    bullets: ['25 active vehicles', '3 workspace users', '2,500 optimized tasks', 'Desktop launch workstation'],
    cta: 'Model Starter',
  },
  {
    name: 'Scale',
    price: '$1,290/mo',
    eyebrow: 'For multi-region operations',
    summary: 'Add deeper exception handling, richer orchestration, and more deliberate operator governance.',
    bullets: ['250 active vehicles', '20 workspace users', '5,000 optimized tasks', 'Priority rollout guidance'],
    cta: 'Model Scale',
  },
  {
    name: 'Enterprise',
    price: 'Custom',
    eyebrow: 'For transformation programs',
    summary: 'Pair premium UI, workspace governance, and tailored launch support with private deployment options.',
    bullets: ['Unlimited regions', 'Dedicated onboarding pod', 'Custom rollout controls', 'Private deployment patterns'],
    cta: 'Talk to FreightPilot',
  },
];

export const faqItems: FaqItem[] = [
  {
    question: 'Is this a route tool, a control tower, or an AI product?',
    answer:
      'It is intentionally all three. FreightPilot uses routing, exception surfaces, desktop launch readiness, and model governance as one operating system instead of treating them as separate categories.',
  },
  {
    question: 'Can we keep our own provider strategy?',
    answer:
      'Yes. The workspace can manage provider keys, switch preferred providers, and preserve a BYOK strategy rather than forcing one model vendor.',
  },
  {
    question: 'What is different about the desktop experience?',
    answer:
      'The desktop layer is not a wrapper for the browser. It is designed as a launch workstation and operator entry point with readiness tracking and environment-specific controls.',
  },
  {
    question: 'How does FreightPilot justify premium positioning?',
    answer:
      'The product is designed around decision quality, operational clarity, and rollout discipline. The design language is cinematic, but the commercial story stays rooted in margin and execution.',
  },
  {
    question: 'Does the site reflect real product capability?',
    answer:
      'Yes. The public experience is built around the routing, alerting, planning, subscription, audit, and launch surfaces that already exist in the platform.',
  },
];

export const launchSteps: TimelineItem[] = [
  {
    label: '01',
    title: 'Create the company workspace',
    detail: 'Provision the owner account, set the operating tier, and define the rollout owner.',
  },
  {
    label: '02',
    title: 'Install the launch workstation',
    detail: 'Give operators a desktop entry point that validates environment setup before first use.',
  },
  {
    label: '03',
    title: 'Wire data, AI, and people',
    detail: 'Connect keys, assign roles, and load warehouses, items, fleet, inventory, and order data.',
  },
  {
    label: '04',
    title: 'Run the first live window',
    detail: 'Move through dry-run routing, readiness verification, and controlled production launch.',
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

export const premiumBadges = ['Apple-grade restraint', 'Linear-class precision', 'Stripe-level clarity', 'OpenAI-style intelligence'];

export const deepLinks = {
  docs: externalLinks.docs,
  console: externalLinks.console,
  desktop: externalLinks.desktop,
};

export const secondaryFeatures: FeatureCard[] = [
  {
    icon: Sparkles,
    title: 'Live visual confidence',
    description: 'Every page is designed to feel like a premium product release, not an admin panel.',
    detail: 'Lighting, motion, and depth carry the brand without compromising readability.',
  },
  {
    icon: Glasses,
    title: 'Glass-first surfaces',
    description: 'Subtle blur, layered depth, and cinematic gradients give the product a distinct identity.',
    detail: 'Use atmosphere to frame information, not to drown it.',
  },
  {
    icon: Waypoints,
    title: 'Launch sequencing',
    description: 'Make every handoff and rollout state explicit in the product experience.',
    detail: 'Premium software should reduce uncertainty as much as it adds capability.',
  },
  {
    icon: Fingerprint,
    title: 'Governance posture',
    description: 'Commercial and AI control surfaces are treated like product features, not buried settings.',
    detail: 'The site and the product tell the same trust story.',
  },
];

export const pageIntro = {
  home: {
    eyebrow: 'FreightPilot 2026',
    title: 'The logistics command layer for teams who want the future to feel real.',
    description:
      'A multi-page product narrative built to feel premium, cinematic, and unmistakably modern while preserving real workspace onboarding and signup functionality.',
  },
};

export const iconLinks = [
  { label: 'Open Console', href: externalLinks.console, icon: ArrowUpRight },
  { label: 'Get Desktop', href: externalLinks.desktop, icon: Boxes },
  { label: 'Read Docs', href: externalLinks.docs, icon: BadgeCheck },
];

export const benefitStrip = [
  'Premium cinematic UI',
  'Route and exception command',
  'AI-first control surface',
  'Workspace launch ritual',
];

export const trustRibbon = ['Audit every action', 'Model every route', 'Launch every workspace deliberately'];

export const platformNarrative = [
  'FreightPilot treats operations, pricing posture, and AI governance as one interface problem.',
  'The website is intentionally designed to feel like a future-facing product announcement, not a brochure.',
  'Every page is purpose-built to reveal a different part of the system while staying visually coherent.',
];

export const pageCards: FeatureCard[] = [
  {
    icon: Compass,
    title: 'Home',
    description: 'A dramatic top-level narrative for the product vision and hero promise.',
    detail: 'Use this page to make the emotional first impression count.',
  },
  {
    icon: Layers3,
    title: 'Platform',
    description: 'A page focused on products, surfaces, workflows, and operational depth.',
    detail: 'Use this page to understand how the stack fits together.',
  },
  {
    icon: Activity,
    title: 'Technology',
    description: 'A page centered on orchestration, models, governance, and intelligence framing.',
    detail: 'Use this page when buyers want to understand the AI substrate.',
  },
  {
    icon: Zap,
    title: 'Pricing + Launch',
    description: 'Commercial clarity and workspace rollout presented with premium polish.',
    detail: 'Use these pages to move from interest into action.',
  },
];
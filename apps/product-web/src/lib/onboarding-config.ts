export type MarketSegment = 'mid-market' | 'local-network' | 'global-enterprise';

export interface OnboardingStep {
  id: string;
  title: string;
  description: string;
}

export interface SegmentConfig {
  segment: MarketSegment;
  displayName: string;
  steps: OnboardingStep[];
}

export const ONBOARDING_CONFIGS: Record<MarketSegment, SegmentConfig> = {
  'mid-market': {
    segment: 'mid-market',
    displayName: 'Mid-Market Business',
    steps: [
      { id: 'business-details', title: 'Business Details', description: 'Tell us about your operations' },
      { id: 'fleet-setup', title: 'Fleet Integration', description: 'Connect your heterogeneous fleet assets' },
      { id: 'regional-routing', title: 'Regional Routing', description: 'Configure regional constraints' },
    ],
  },
  'local-network': {
    segment: 'local-network',
    displayName: 'Local Logistics Network',
    steps: [
      { id: 'network-profile', title: 'Network Profile', description: 'Define your operating area' },
      { id: 'driver-onboarding', title: 'Driver Roster', description: 'Import your local drivers' },
      { id: 'zone-mapping', title: 'Zone Mapping', description: 'Map out your primary delivery zones' },
    ],
  },
  'global-enterprise': {
    segment: 'global-enterprise',
    displayName: 'Global Corporation',
    steps: [
      { id: 'sso-setup', title: 'SSO Configuration', description: 'Setup enterprise single sign-on' },
      { id: 'multi-region', title: 'Multi-Region Setup', description: 'Configure global operating regions' },
      { id: 'api-integration', title: 'API Integration', description: 'Connect your existing ERP/WMS systems' },
    ],
  }
};

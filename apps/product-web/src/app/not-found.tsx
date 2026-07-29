import { MagneticLink } from '@/components/site/magnetic-link';
import { PageHero } from '@/components/site/page-hero';

export default function NotFound() {
  return (
    <PageHero
      eyebrow="Lost in orbit"
      title="This page drifted out of the launch path."
      description="Return to the core narrative, explore the platform pages, or move directly into the workspace launch flow."
      actions={
        <>
          <MagneticLink href="/" variant="primary">
            Back to home
          </MagneticLink>
          <MagneticLink href="/launch" variant="secondary">
            Open launch page
          </MagneticLink>
        </>
      }
    />
  );
}
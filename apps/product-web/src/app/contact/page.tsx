import { Mail } from 'lucide-react';

import { ContactForm } from '@/components/site/contact-form';
import { PageHero } from '@/components/site/page-hero';
import { SpotlightCard } from '@/components/site/spotlight-card';

export default function ContactPage() {
  return (
    <>
      <PageHero
        eyebrow="Get in touch"
        title="Send us a message"
        description="We read every message. Replies are manual and may take a few days."
      />

      <section className="section-shell pb-16 pt-8 sm:pb-24 sm:pt-12">
        <div className="grid gap-12 lg:grid-cols-[1fr_1.2fr] lg:gap-16">
          <div className="space-y-8">
            <div>
              <h2 className="font-display text-2xl text-white">How can we help?</h2>
              <p className="mt-3 text-sm leading-7 text-white/60">
                Fill out the form and we will read your message. Replies are manual and may take a
                few days. For technical questions, check the documentation links in the footer.
              </p>
            </div>

            <div className="space-y-4">
              <SpotlightCard className="flex items-start gap-4 p-5">
                <div className="inline-flex rounded-lg bg-cyan-400/10 p-2.5">
                  <Mail className="h-5 w-5 text-cyan-400" />
                </div>
                <div>
                  <h3 className="font-medium text-white">Email us</h3>
                  <p className="mt-1 text-sm text-white/60">nahomgwmichael@gmail.com</p>
                </div>
              </SpotlightCard>
            </div>
          </div>

          <div className="glass-panel rounded-[32px] p-6 sm:p-8 lg:p-10">
            <h3 className="mb-6 font-display text-xl text-white">Send a message</h3>
            <ContactForm />
          </div>
        </div>
      </section>
    </>
  );
}

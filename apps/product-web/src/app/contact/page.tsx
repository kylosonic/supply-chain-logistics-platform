import { Mail, MapPin, Phone } from 'lucide-react';

import { ContactForm } from '@/components/site/contact-form';
import { PageHero } from '@/components/site/page-hero';
import { SpotlightCard } from '@/components/site/spotlight-card';

export default function ContactPage() {
  return (
    <>
      <PageHero
        eyebrow="Get in touch"
        title="Connect with our team."
        description="Whether you're looking for a custom enterprise rollout, partnership details, or have a question about the platform, our team is ready to help."
      />

      <section className="section-shell pb-16 pt-8 sm:pb-24 sm:pt-12">
        <div className="grid gap-12 lg:grid-cols-[1fr_1.2fr] lg:gap-16">
          
          <div className="space-y-8">
            <div>
              <h2 className="font-display text-2xl text-white">How can we help?</h2>
              <p className="mt-3 text-sm leading-7 text-white/60">
                Please fill out the form, and a member of our logistics solutions team will reach out within 24 hours. For technical support, please visit our documentation or open a ticket in your console.
              </p>
            </div>
            
            <div className="space-y-4">
              <SpotlightCard className="flex items-start gap-4 p-5">
                <div className="inline-flex rounded-lg bg-cyan-400/10 p-2.5">
                  <Mail className="h-5 w-5 text-cyan-400" />
                </div>
                <div>
                  <h3 className="font-medium text-white">Email Us</h3>
                  <p className="mt-1 text-sm text-white/60">nahomgwmichael@gmail.com</p>
                </div>
              </SpotlightCard>

              <SpotlightCard className="flex items-start gap-4 p-5">
                <div className="inline-flex rounded-lg bg-violet-400/10 p-2.5">
                  <Phone className="h-5 w-5 text-violet-400" />
                </div>
                <div>
                  <h3 className="font-medium text-white">Call Us</h3>
                  <p className="mt-1 text-sm text-white/60">+1 (800) 555-0199</p>
                </div>
              </SpotlightCard>

              <SpotlightCard className="flex items-start gap-4 p-5">
                <div className="inline-flex rounded-lg bg-amber-400/10 p-2.5">
                  <MapPin className="h-5 w-5 text-amber-400" />
                </div>
                <div>
                  <h3 className="font-medium text-white">Headquarters</h3>
                  <p className="mt-1 text-sm text-white/60">
                    100 Logistics Way<br />
                    Suite 400<br />
                    San Francisco, CA 94107
                  </p>
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

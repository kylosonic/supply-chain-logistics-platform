import type { Metadata } from 'next';
import { Inter, Space_Grotesk } from 'next/font/google';
import type { PropsWithChildren } from 'react';

import { SiteChrome } from '@/components/site/site-chrome';

import './globals.css';

const inter = Inter({ subsets: ['latin'], variable: '--font-inter' });
const spaceGrotesk = Space_Grotesk({ subsets: ['latin'], variable: '--font-space-grotesk' });

export const metadata: Metadata = {
  title: {
    default: 'FreightPilot | Futuristic AI Logistics Control Layer',
    template: '%s | FreightPilot',
  },
  description:
    'FreightPilot is a premium AI logistics command layer built for operators who need futuristic control, margin-aware routing, and enterprise launch readiness.',
};

export default function RootLayout({ children }: PropsWithChildren) {
  return (
    <html lang="en" className={`${inter.variable} ${spaceGrotesk.variable}`}>
      <body className="font-sans antialiased">
        <SiteChrome>{children}</SiteChrome>
      </body>
    </html>
  );
}
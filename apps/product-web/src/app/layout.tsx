import type { Metadata, Viewport } from 'next';
import { Inter, Space_Grotesk } from 'next/font/google';
import type { PropsWithChildren } from 'react';

import { MotionProvider } from '@/components/site/motion-provider';
import { SiteChrome } from '@/components/site/site-chrome';

import './globals.css';

const inter = Inter({ subsets: ['latin'], variable: '--font-inter' });
const spaceGrotesk = Space_Grotesk({ subsets: ['latin'], variable: '--font-space-grotesk' });

const siteUrl = process.env.NEXT_PUBLIC_SITE_URL || 'https://freightpilot.com';

const siteDescription =
  'Sign up and your workspace loads with sample data — warehouses, fleet, inventory, orders, all ready. Optimize your first route immediately.';

export const metadata: Metadata = {
  metadataBase: new URL(siteUrl),
  title: {
    default: 'FreightPilot — Run your first optimized route in 5 minutes. Free.',
    template: '%s | FreightPilot',
  },
  description: siteDescription,
  keywords: [
    'logistics platform',
    'route optimization',
    'supply chain management',
    'freight management',
    'AI logistics',
    'fleet management',
    'dispatch software',
  ],
  authors: [{ name: 'FreightPilot' }],
  creator: 'FreightPilot',
  openGraph: {
    type: 'website',
    locale: 'en_US',
    url: siteUrl,
    siteName: 'FreightPilot',
    title: 'FreightPilot — Run your first optimized route in 5 minutes. Free.',
    description: siteDescription,
    images: [
      {
        url: '/og-image.png',
        width: 1200,
        height: 630,
        alt: 'FreightPilot — Run your first optimized route in 5 minutes. Free.',
      },
    ],
  },
  twitter: {
    card: 'summary_large_image',
    title: 'FreightPilot — Run your first optimized route in 5 minutes. Free.',
    description: siteDescription,
    images: ['/og-image.png'],
  },
  robots: {
    index: true,
    follow: true,
    googleBot: {
      index: true,
      follow: true,
      'max-video-preview': -1,
      'max-image-preview': 'large',
      'max-snippet': -1,
    },
  },
  icons: {
    icon: [{ url: '/favicon.svg', type: 'image/svg+xml' }],
    apple: '/apple-touch-icon.png',
  },
};

export const viewport: Viewport = {
  themeColor: '#050505',
  width: 'device-width',
  initialScale: 1,
};

export default function RootLayout({ children }: PropsWithChildren) {
  return (
    <html lang="en" className={`${inter.variable} ${spaceGrotesk.variable}`}>
      <body className="font-sans antialiased">
        <a href="#main-content" className="skip-to-content">
          Skip to content
        </a>
        <MotionProvider>
          <SiteChrome>{children}</SiteChrome>
        </MotionProvider>
      </body>
    </html>
  );
}
import type { Config } from 'tailwindcss';

const config: Config = {
  content: ['./src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        base: {
          950: '#050505',
          925: '#0B0B0B',
          900: '#101010',
        },
      },
      boxShadow: {
        luxe: '0 24px 80px rgba(0, 0, 0, 0.45)',
        glow: '0 0 0 1px rgba(96, 165, 250, 0.24), 0 22px 70px rgba(59, 130, 246, 0.22)',
      },
      backgroundImage: {
        aurora:
          'radial-gradient(circle at 15% 20%, rgba(59,130,246,0.22), transparent 28%), radial-gradient(circle at 85% 12%, rgba(168,85,247,0.18), transparent 26%), radial-gradient(circle at 50% 100%, rgba(34,211,238,0.14), transparent 30%)',
      },
      fontFamily: {
        sans: ['var(--font-inter)', 'Inter', 'system-ui', 'sans-serif'],
        display: ['var(--font-space-grotesk)', 'Space Grotesk', 'sans-serif'],
      },
    },
  },
  plugins: [],
};

export default config;
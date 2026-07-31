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
        'glow-lg':
          '0 0 0 1px rgba(96, 165, 250, 0.20), 0 0 30px rgba(56, 189, 248, 0.15), 0 28px 80px rgba(59, 130, 246, 0.18)',
      },
      backgroundImage: {
        aurora:
          'radial-gradient(circle at 15% 20%, rgba(59,130,246,0.22), transparent 28%), radial-gradient(circle at 85% 12%, rgba(168,85,247,0.18), transparent 26%), radial-gradient(circle at 50% 100%, rgba(34,211,238,0.14), transparent 30%)',
      },
      fontFamily: {
        sans: ['var(--font-inter)', 'Inter', 'system-ui', 'sans-serif'],
        display: ['var(--font-space-grotesk)', 'Space Grotesk', 'sans-serif'],
      },
      keyframes: {
        shimmer: {
          '0%': { backgroundPosition: '-200% 0' },
          '100%': { backgroundPosition: '200% 0' },
        },
        float: {
          '0%, 100%': { transform: 'translateY(0)' },
          '50%': { transform: 'translateY(-8px)' },
        },
        'pulse-glow': {
          '0%, 100%': { opacity: '0.6' },
          '50%': { opacity: '1' },
        },
      },
      animation: {
        shimmer: 'shimmer 3s ease-in-out infinite',
        float: 'float 4s ease-in-out infinite',
        'pulse-glow': 'pulse-glow 2.5s ease-in-out infinite',
      },
    },
  },
  plugins: [],
};

export default config;
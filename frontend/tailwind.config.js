/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        nexus: {
          bg: '#000000',
          card: '#0A0A0A',
          border: '#1a1a1a',
          'border-light': '#2a2a2a',
          cyan: '#00E5FF',
          amber: '#FFB800',
          green: '#00E676',
          red: '#FF3D57',
          'dark-bg': '#0D0F14',
          'dark-card': '#141820',
          'dark-border': '#1E2530',
        },
      },
      fontFamily: {
        sans: ['"General Sans"', 'system-ui', 'sans-serif'],
        heading: ['"Syne"', 'system-ui', 'sans-serif'],
        mono: ['"JetBrains Mono"', 'monospace'],
        display: ['"Playfair Display"', 'serif'],
      },
      animation: {
        'glow-pulse': 'glow-pulse 2s ease-in-out infinite alternate',
        'fade-in': 'fade-in 0.6s ease-out',
        'slide-up': 'slide-up 0.6s ease-out',
        'slide-in-right': 'slide-in-right 0.5s ease-out',
        'count-up': 'count-up 1s ease-out',
        ticker: 'ticker 30s linear infinite',
      },
      keyframes: {
        'glow-pulse': {
          '0%': { boxShadow: '0 0 5px rgba(0,229,255,0.2)' },
          '100%': { boxShadow: '0 0 20px rgba(0,229,255,0.4)' },
        },
        'fade-in': {
          '0%': { opacity: '0', transform: 'translateY(20px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        'slide-up': {
          '0%': { opacity: '0', transform: 'translateY(40px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        'slide-in-right': {
          '0%': { opacity: '0', transform: 'translateX(30px)' },
          '100%': { opacity: '1', transform: 'translateX(0)' },
        },
        ticker: {
          '0%': { transform: 'translateX(0)' },
          '100%': { transform: 'translateX(-50%)' },
        },
      },
    },
  },
  plugins: [],
};

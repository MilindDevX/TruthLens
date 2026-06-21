/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Inter', '-apple-system', 'BlinkMacSystemFont', 'sans-serif'],
      },
      colors: {
        surface: {
          primary: '#0a0e1a',
          secondary: '#111827',
          card: 'rgba(17, 24, 39, 0.6)',
          glass: 'rgba(255, 255, 255, 0.04)',
          'glass-hover': 'rgba(255, 255, 255, 0.08)',
        },
        border: {
          glass: 'rgba(255, 255, 255, 0.08)',
          'glass-hover': 'rgba(255, 255, 255, 0.15)',
        },
        accent: {
          cyan: '#06b6d4',
          'cyan-dim': 'rgba(6, 182, 212, 0.15)',
          violet: '#8b5cf6',
          'violet-dim': 'rgba(139, 92, 246, 0.15)',
        },
      },
      boxShadow: {
        'glow-cyan': '0 0 20px rgba(6, 182, 212, 0.3)',
        'glow-violet': '0 0 20px rgba(139, 92, 246, 0.3)',
        'glass': '0 8px 32px rgba(0, 0, 0, 0.4)',
      },
      animation: {
        'fade-in': 'fadeIn 0.4s ease-out',
        'slide-up': 'slideUp 0.4s ease-out',
        'spin-slow': 'spin 2s linear infinite',
        'mesh-1': 'meshFloat 20s ease-in-out infinite',
        'mesh-2': 'meshFloat 25s ease-in-out infinite reverse',
        'gauge-fill': 'gaugeFill 1s cubic-bezier(0.34, 1.56, 0.64, 1) forwards',
      },
      keyframes: {
        fadeIn: {
          from: { opacity: '0', transform: 'translateY(12px)' },
          to: { opacity: '1', transform: 'translateY(0)' },
        },
        slideUp: {
          from: { opacity: '0', transform: 'translateY(24px)' },
          to: { opacity: '1', transform: 'translateY(0)' },
        },
        meshFloat: {
          '0%, 100%': { transform: 'translate(0, 0)' },
          '50%': { transform: 'translate(40px, -30px)' },
        },
        gaugeFill: {
          from: { strokeDashoffset: '283' },
        },
      },
    },
  },
  plugins: [],
}

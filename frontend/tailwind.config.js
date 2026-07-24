/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Clean white Claude-style theme
        bg: {
          primary: '#FFFFFF',
          secondary: '#F7F7F8',
          tertiary: '#EFEFEF',
        },
        surface: {
          DEFAULT: '#FFFFFF',
          hover: '#F5F5F5',
          active: '#EBEBEB',
        },
        border: {
          DEFAULT: '#E5E5E5',
          strong: '#CCCCCC',
        },
        text: {
          primary: '#1A1A1A',
          secondary: '#6B6B6B',
          muted: '#9B9B9B',
          inverse: '#FFFFFF',
        },
        brand: {
          DEFAULT: '#7C3AED',
          light: '#8B5CF6',
          dark: '#6D28D9',
          50: '#F5F3FF',
          100: '#EDE9FE',
          200: '#DDD6FE',
        },
        accent: {
          blue: '#2563EB',
          emerald: '#059669',
          amber: '#D97706',
          red: '#DC2626',
          violet: '#7C3AED',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'Fira Code', 'monospace'],
        display: ['Cal Sans', 'Inter', 'system-ui', 'sans-serif'],
      },
      boxShadow: {
        'soft': '0 1px 3px rgba(0,0,0,0.06), 0 1px 2px rgba(0,0,0,0.04)',
        'card': '0 4px 16px rgba(0,0,0,0.08), 0 1px 4px rgba(0,0,0,0.04)',
        'card-hover': '0 8px 32px rgba(0,0,0,0.12), 0 2px 8px rgba(0,0,0,0.06)',
        'brand': '0 4px 20px rgba(124,58,237,0.25)',
        'brand-lg': '0 8px 40px rgba(124,58,237,0.35)',
        'float': '0 20px 60px rgba(0,0,0,0.15), 0 8px 24px rgba(0,0,0,0.08)',
        'inner-soft': 'inset 0 1px 3px rgba(0,0,0,0.05)',
        '3d': '0 20px 60px rgba(0,0,0,0.2), 0 8px 24px rgba(0,0,0,0.1), 0 2px 6px rgba(0,0,0,0.08)',
      },
      backgroundImage: {
        'gradient-brand': 'linear-gradient(135deg, #7C3AED 0%, #2563EB 100%)',
        'gradient-brand-soft': 'linear-gradient(135deg, #F5F3FF 0%, #EFF6FF 100%)',
        'gradient-mesh': 'radial-gradient(at 40% 20%, hsla(270,80%,70%,0.15) 0px, transparent 50%), radial-gradient(at 80% 0%, hsla(220,80%,70%,0.1) 0px, transparent 50%), radial-gradient(at 0% 50%, hsla(270,60%,60%,0.08) 0px, transparent 50%)',
        'gradient-radial': 'radial-gradient(var(--tw-gradient-stops))',
      },
      animation: {
        'float': 'float 6s ease-in-out infinite',
        'float-slow': 'float 9s ease-in-out infinite',
        'float-reverse': 'float-reverse 7s ease-in-out infinite',
        'spin-slow': 'spin 20s linear infinite',
        'pulse-brand': 'pulse-brand 2s ease-in-out infinite',
        'slide-up': 'slide-up 0.5s ease-out',
        'slide-in-right': 'slide-in-right 0.4s ease-out',
        'fade-in': 'fade-in 0.4s ease-out',
        'scale-in': 'scale-in 0.3s ease-out',
        'shimmer': 'shimmer 2s infinite',
        'typing': 'typing 1.4s ease-in-out infinite',
        'counter': 'counter 2s ease-out forwards',
        'orbit': 'orbit 8s linear infinite',
        'orbit-reverse': 'orbit-reverse 12s linear infinite',
        'morph': 'morph 8s ease-in-out infinite',
      },
      keyframes: {
        float: {
          '0%, 100%': { transform: 'translateY(0px)' },
          '50%': { transform: 'translateY(-20px)' },
        },
        'float-reverse': {
          '0%, 100%': { transform: 'translateY(0px)' },
          '50%': { transform: 'translateY(20px)' },
        },
        'pulse-brand': {
          '0%, 100%': { boxShadow: '0 0 0 0 rgba(124,58,237,0.4)' },
          '50%': { boxShadow: '0 0 0 12px rgba(124,58,237,0)' },
        },
        'slide-up': {
          from: { opacity: '0', transform: 'translateY(30px)' },
          to: { opacity: '1', transform: 'translateY(0)' },
        },
        'slide-in-right': {
          from: { opacity: '0', transform: 'translateX(20px)' },
          to: { opacity: '1', transform: 'translateX(0)' },
        },
        'fade-in': {
          from: { opacity: '0' },
          to: { opacity: '1' },
        },
        'scale-in': {
          from: { opacity: '0', transform: 'scale(0.95)' },
          to: { opacity: '1', transform: 'scale(1)' },
        },
        shimmer: {
          '0%': { backgroundPosition: '-200% 0' },
          '100%': { backgroundPosition: '200% 0' },
        },
        typing: {
          '0%, 60%, 100%': { transform: 'translateY(0)', opacity: '0.4' },
          '30%': { transform: 'translateY(-4px)', opacity: '1' },
        },
        orbit: {
          from: { transform: 'rotate(0deg) translateX(120px) rotate(0deg)' },
          to: { transform: 'rotate(360deg) translateX(120px) rotate(-360deg)' },
        },
        'orbit-reverse': {
          from: { transform: 'rotate(0deg) translateX(180px) rotate(0deg)' },
          to: { transform: 'rotate(-360deg) translateX(180px) rotate(360deg)' },
        },
        morph: {
          '0%, 100%': { borderRadius: '60% 40% 30% 70% / 60% 30% 70% 40%' },
          '25%': { borderRadius: '30% 60% 70% 40% / 50% 60% 30% 60%' },
          '50%': { borderRadius: '50% 60% 30% 60% / 40% 30% 70% 50%' },
          '75%': { borderRadius: '60% 40% 60% 30% / 60% 70% 30% 40%' },
        },
      },
    },
  },
  plugins: [],
}
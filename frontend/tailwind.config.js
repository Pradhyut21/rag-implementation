/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        dark: '#0f1115',
        panel: '#1a1d24',
        border: '#2a2d36',
        primary: '#3b82f6',
        accent: '#8b5cf6',
      }
    },
  },
  plugins: [],
}
/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx,ts,tsx}'],
  theme: {
    extend: {
      fontFamily: {
        display: ['"Playfair Display"', 'Georgia', 'serif'],
        body: ['"Source Serif 4"', 'Georgia', 'serif'],
        mono: ['"JetBrains Mono"', 'monospace'],
      },
      colors: {
        ink: {
          DEFAULT: '#1a1208',
          light: '#3d2f1a',
        },
        parchment: {
          DEFAULT: '#f5f0e8',
          dark: '#e8dfc8',
          darker: '#d4c9a8',
        },
        crimson: {
          DEFAULT: '#8b1a1a',
          light: '#b52b2b',
        },
        gold: {
          DEFAULT: '#c8932a',
          light: '#e4b04a',
        },
        sage: '#4a6741',
        slate: '#3d4f5c',
      },
      boxShadow: {
        paper: '0 2px 8px rgba(26, 18, 8, 0.12), 0 0 0 1px rgba(26, 18, 8, 0.06)',
        'paper-hover': '0 4px 16px rgba(26, 18, 8, 0.18), 0 0 0 1px rgba(26, 18, 8, 0.1)',
      },
    },
  },
  plugins: [],
}

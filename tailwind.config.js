/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{vue,js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        'display': ['Noto Serif SC', 'Georgia', 'serif'],
        'body': ['Noto Sans SC', 'system-ui', 'sans-serif'],
        'mono': ['JetBrains Mono', 'Consolas', 'monospace'],
      },
      colors: {
        'finance': {
          'green': '#10B981',
          'red': '#EF4444',
          'gold': '#F59E0B',
          'slate': '#1E293B',
        }
      }
    },
  },
  plugins: [],
}
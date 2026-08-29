/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        brand: {
          50: '#f0f7ff',
          100: '#e0effe',
          200: '#bae0fd',
          300: '#7cc8fc',
          400: '#36abf8',
          500: '#0c8fe9',
          600: '#0170c7',
          700: '#0259a1',
          800: '#064c84',
          900: '#0b406e',
          950: '#072849',
        },
        surface: {
          light: '#f8fafc',
          card: '#ffffff',
          dark: '#0f172a',
          darkCard: '#1e293b',
          darkHover: '#334155'
        }
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'sans-serif'],
      }
    },
  },
  plugins: [],
}

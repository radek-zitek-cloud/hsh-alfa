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
        primary: {
          light: '#ffffff',
          dark: '#1a1a1a',
        },
        secondary: {
          light: '#f5f5f5',
          dark: '#2d2d2d',
        },
        accent: {
          light: '#0066cc',
          dark: '#4a9eff',
        }
      }
    },
  },
  plugins: [],
}

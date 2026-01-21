/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./pages/algoflow/**/*.{html,js}"],
  theme: {
    extend: {
      colors: {
        primary: '#0A091B',
        accent: {
          teal: '#2DD4BF',
          emerald: '#10B981',
          blue: '#60A5FA'
        }
      },
      fontFamily: {
        sans: ['Inter', 'sans-serif'],
        display: ['Space Grotesk', 'sans-serif'],
      },
      animation: {
        'pulse-slow': 'pulse 8s cubic-bezier(0.4, 0, 0.6, 1) infinite',
      }
    },
  },
  plugins: [],
}

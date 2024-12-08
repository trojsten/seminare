/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./seminare/**/*.{html,js}"],
  theme: {
    extend: {
      colors: {
        "primary": "var(--primary)",
        "primary-light": "var(--primary-light)",
        "primary-dark": "var(--primary-dark)",
        "primary-text": "var(--primary-text)",
      },
      fontFamily: {
        sans: ['"Source Sans Pro"', 'sans-serif'],
      },
      typography: {
        DEFAULT: {
          css: {
            maxWidth: '75ch',
          },
        },
      }
    },
  },
  plugins: [
    require('@tailwindcss/forms'),
    require('@tailwindcss/typography'),
  ],
}

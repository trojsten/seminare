/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./seminare/**/*.{html,js}"],
  theme: {
    extend: {},
  },
  plugins: [
    require('@tailwindcss/forms'),
    require('@tailwindcss/typography'),
  ],
}

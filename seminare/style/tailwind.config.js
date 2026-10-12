/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./seminare/**/*.{html,js,py}"],
  theme: {
    extend: {
      typography: {
        DEFAULT: {
          css: {
            maxWidth: '75ch',
            'code::before': {
              content: '',
            },
            'code::after': {
              content: '',
            },
          },
        },
      },
      maxWidth: {
        'prose': '75ch',
      },
    },
  },
}

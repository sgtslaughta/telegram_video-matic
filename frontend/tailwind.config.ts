import type { Config } from 'tailwindcss'

export default {
  content: [
    './index.html',
    './src/**/*.{js,ts,jsx,tsx}',
  ],
  theme: {
    extend: {
      colors: {
        telegramBlue: '#229ed9',
      },
    },
  },
  plugins: [],
} satisfies Config

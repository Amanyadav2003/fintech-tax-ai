/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ['./src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        navy: { 50: '#eef4fa', 100: '#d9e6f3', 500: '#2d5f8b', 700: '#1e3a5f', 900: '#102a43' },
        mint: { 50: '#ecfdf5', 500: '#10b981', 700: '#047857' },
        ink: '#152536',
      },
      boxShadow: {
        soft: '0 18px 45px rgba(16, 42, 67, 0.10)',
      },
    },
  },
  plugins: [],
};

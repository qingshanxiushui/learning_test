/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ocean: {
          50: "#f0f7ff",
          100: "#dcecff",
          600: "#1f6ed4",
          700: "#1859ad"
        }
      }
    }
  },
  plugins: []
};

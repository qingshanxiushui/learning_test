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
        },
        brand: {
          cream: "#FAF6EE",
          paper: "#FDFBF7",
          ink: "#1C3134",
          inkSoft: "#4A463F",
          inkMuted: "#857E74",
          teal: "#24665C",
          tealDeep: "#004E45",
          persimmon: "#D96A43",
          ginkgo: "#E0A838",
          line: "#EDE7DC",
          lineSoft: "#F2ECE1"
        }
      },
      fontFamily: {
        kai: ['"Kaiti SC"', "STKaiti", "KaiTi", '"Noto Serif SC"', "serif"],
        sans: [
          '"PingFang SC"',
          '"HarmonyOS Sans"',
          '"Microsoft YaHei"',
          '"Noto Sans SC"',
          "sans-serif"
        ]
      },
      boxShadow: {
        soft: "0 8px 24px -4px rgba(28,49,52,0.06), 0 2px 6px -1px rgba(28,49,52,0.04)",
        hover:
          "0 20px 32px -8px rgba(28,49,52,0.12), 0 6px 12px -2px rgba(28,49,52,0.06)",
        glow: "0 8px 25px -4px rgba(36,102,92,0.45)"
      },
      keyframes: {
        "gentle-pulse": {
          "0%, 100%": { transform: "scale(1)" },
          "50%": { transform: "scale(1.02)" }
        }
      },
      animation: {
        "gentle-pulse": "gentle-pulse 3s ease-in-out infinite"
      }
    }
  },
  plugins: []
};

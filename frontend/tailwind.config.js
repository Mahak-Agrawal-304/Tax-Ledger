/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        paper: "#EFECDD",
        "paper-line": "#DCD7C2",
        ink: "#1B2E28",
        "ink-muted": "#5B6A62",
        ledger: "#2B5D50",
        "ledger-dark": "#1E4238",
        rupee: "#5B4636",
        marigold: "#C98A2C",
        brick: "#8C3A2B",
      },
      fontFamily: {
        display: ["Fraunces", "serif"],
        sans: ["IBM Plex Sans", "system-ui", "sans-serif"],
        mono: ["IBM Plex Mono", "ui-monospace", "monospace"],
      },
      borderRadius: {
        sm: "2px",
        DEFAULT: "3px",
      },
    },
  },
  plugins: [],
};

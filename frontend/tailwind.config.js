/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        arango: {
          // Greens (primary & actions)
          "green-bg": "#f4fef2",
          green: "#006532",
          "green-hover": "#005329",
          "green-brand": "#007339",
          // Grays (text & layout)
          page: "#ffffff",
          panel: "#f8f8f8",
          border: "#e5e5e5",
          text: "#282828",
          muted: "#9a9a9a",
          // Interface specifics
          error: "#da1a20",
          menu: "#000000",
        },
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "sans-serif"],
        mono: ["Courier New", "Courier", "monospace"],
      },
    },
  },
  plugins: [],
};

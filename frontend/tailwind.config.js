/** @type {import('tailwindcss').Config} */
export default {
  darkMode: ["class"],
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        background: {
          DEFAULT: "var(--bg-primary)",
          subtle: "var(--bg-subtle)",
        },
        surface: {
          DEFAULT: "var(--surface-bg)",
          elevated: "var(--surface-elevated)",
          border: "var(--surface-border)",
        },
        brand: {
          primary: "var(--brand-primary)",
          hover: "var(--brand-hover)",
          secondary: "var(--brand-secondary)",
        },
        text: {
          primary: "var(--text-primary)",
          secondary: "var(--text-secondary)",
          muted: "var(--text-muted)",
        },
      },
      fontFamily: {
        sans: ["Inter", "-apple-system", "BlinkMacSystemFont", "Segoe UI", "Roboto", "sans-serif"],
      },
    },
  },
  plugins: [],
}

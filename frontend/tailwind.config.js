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
        forma: {
          navy: "#17263C",
          "deep-navy": "#101B2B",
          ivory: "#F7F5F0",
          "ivory-subtle": "#EFECE6",
          white: "#FFFFFF",
          muted: "#687386",
          border: "#E5E7EB",
          "border-dark": "#1F2D40",
          emerald: "#315C4B",
          "emerald-light": "#E8F0EB",
          "emerald-hover": "#26483B",
          gold: "#B79A65",
          "gold-light": "#F7F3EB",
          "gold-dark": "#8F7546",
        },
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
          gold: "var(--brand-gold)",
        },
        text: {
          primary: "var(--text-primary)",
          secondary: "var(--text-secondary)",
          muted: "var(--text-muted)",
        },
      },
      fontFamily: {
        serif: ["Newsreader", "Playfair Display", "Georgia", "serif"],
        sans: ["Plus Jakarta Sans", "Inter", "-apple-system", "BlinkMacSystemFont", "sans-serif"],
      },
      boxShadow: {
        subtle: "0 1px 3px rgba(16, 27, 43, 0.04), 0 1px 2px rgba(16, 27, 43, 0.02)",
        card: "0 4px 20px -2px rgba(16, 27, 43, 0.05), 0 2px 6px -1px rgba(16, 27, 43, 0.02)",
        elevated: "0 20px 30px -10px rgba(16, 27, 43, 0.08), 0 10px 10px -5px rgba(16, 27, 43, 0.03)",
        glow: "0 0 25px -5px rgba(183, 154, 101, 0.25)",
      },
      borderRadius: {
        forma: "0.625rem", // 10px tailored radius
      },
    },
  },
  plugins: [],
}

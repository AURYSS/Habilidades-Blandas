import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        brand: {
          50: "#effafa",
          100: "#d7f2f4",
          200: "#b4e4ea",
          300: "#82cfda",
          400: "#49b2c3",
          500: "#2d96a8",
          600: "#28798e",
          700: "#276274",
          800: "#27515f",
          900: "#204450",
          950: "#122b34",
        },
        gold: {
          400: "#e4b843",
          500: "#d4a72c",
          600: "#b88921",
        },
        ink: {
          950: "#0b1219",
          900: "#111c29",
          800: "#1b2c3c",
          700: "#29435a",
        },
      },
      fontFamily: {
        sans: ["var(--font-inter)", "system-ui", "sans-serif"],
      },
      boxShadow: {
        card: "0 1px 2px 0 rgb(16 24 40 / 0.04), 0 1px 3px 0 rgb(16 24 40 / 0.08)",
        lift: "0 8px 24px -6px rgb(16 24 40 / 0.16)",
      },
    },
  },
  plugins: [],
};
export default config;
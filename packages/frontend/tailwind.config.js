/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        aegis: {
          dark: "#0a0e1a",
          card: "#111827",
          border: "#1f2937",
          accent: "#3b82f6",
          green: "#10b981",
          yellow: "#f59e0b",
          red: "#ef4444",
          critical: "#dc2626",
        },
      },
      animation: {
        pulse: "pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite",
      },
    },
  },
  plugins: [],
};

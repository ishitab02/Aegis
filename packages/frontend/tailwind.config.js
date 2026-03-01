/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        // Background layers (dark to light)
        bg: {
          base: "#0a0a0b",
          surface: "#111113",
          elevated: "#18181b",
          overlay: "#1f1f23",
        },
        // Borders
        border: {
          subtle: "#27272a",
          muted: "#3f3f46",
        },
        // Text hierarchy
        text: {
          primary: "#fafafa",
          secondary: "#a1a1aa",
          muted: "#71717a",
          disabled: "#52525b",
        },
        // Semantic colors
        threat: {
          critical: "#ef4444",
          "critical-muted": "#7f1d1d",
          high: "#f97316",
          "high-muted": "#7c2d12",
          medium: "#eab308",
          "medium-muted": "#713f12",
          low: "#52525b",
          "low-muted": "#27272a",
        },
        success: {
          DEFAULT: "#22c55e",
          muted: "#14532d",
        },
        accent: {
          DEFAULT: "#3b82f6",
          hover: "#2563eb",
        },
      },
      fontFamily: {
        sans: [
          "Inter",
          "ui-sans-serif",
          "system-ui",
          "-apple-system",
          "sans-serif",
        ],
        mono: [
          "JetBrains Mono",
          "Fira Code",
          "ui-monospace",
          "SFMono-Regular",
          "monospace",
        ],
      },
      fontSize: {
        "2xs": ["0.625rem", { lineHeight: "1rem" }], // 10px
      },
      spacing: {
        18: "4.5rem",
        88: "22rem",
      },
      animation: {
        "pulse-slow": "pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite",
        "fade-in": "fadeIn 0.2s ease-out",
        "slide-up": "slideUp 0.2s ease-out",
        "slide-down": "slideDown 0.15s ease-out",
        "scale-in": "scaleIn 0.15s ease-out",
        shimmer: "shimmer 2s linear infinite",
      },
      keyframes: {
        fadeIn: {
          "0%": { opacity: "0" },
          "100%": { opacity: "1" },
        },
        slideUp: {
          "0%": { opacity: "0", transform: "translateY(8px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        slideDown: {
          "0%": { opacity: "0", transform: "translateY(-4px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        scaleIn: {
          "0%": { opacity: "0", transform: "scale(0.95)" },
          "100%": { opacity: "1", transform: "scale(1)" },
        },
        shimmer: {
          "0%": { backgroundPosition: "-200% 0" },
          "100%": { backgroundPosition: "200% 0" },
        },
      },
      boxShadow: {
        glow: "0 0 20px rgba(59, 130, 246, 0.15)",
        "glow-critical": "0 0 20px rgba(239, 68, 68, 0.2)",
        dropdown:
          "0 4px 6px -1px rgba(0, 0, 0, 0.3), 0 2px 4px -2px rgba(0, 0, 0, 0.3)",
      },
      backdropBlur: {
        xs: "2px",
      },
    },
  },
  plugins: [],
};

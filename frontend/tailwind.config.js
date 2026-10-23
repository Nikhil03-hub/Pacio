module.exports = {
  content: ["./src/**/*.{js,jsx,ts,tsx}"],
  theme: {
    extend: {
      colors: {
        // DEFAULT keys matter: ink/bone were bare scales, so every `bg-ink`,
        // `text-bone`, `border-ink` and `bg-ink/40` usage (primary buttons, modal
        // scrims, dark panels) silently resolved to nothing.
        // ink-400 is darkened from #9a9a9a to #767676: it is the app's muted-label
        // colour (606 uses, often at 9-10px) and failed WCAG AA at 2.8:1.
        ink: {
          DEFAULT: "#0a0a0a",
          900: "#0a0a0a",
          800: "#1a1a1a",
          700: "#2a2a2a",
          600: "#555555",
          500: "#666666",
          400: "#767676",
          300: "#b3b3b3",
          200: "#d9d9d9",
        },
        bone: {
          DEFAULT: "#f5f3ee",
          50: "#ffffff",
          100: "#f5f3ee",
          200: "#ecebe5",
          300: "#dedbd1",
        },
        paper: "#ffffff",
        accent: {
          DEFAULT: "#ff3b00",
          hover: "#e03400",
          soft: "#ffe5d9",
        },
        rust: "#c1440e",
        moss: "#4a5d3a",
        ochre: "#d4a017",
        line: "rgba(10,10,10,0.10)",
        "line-strong": "rgba(10,10,10,0.18)",
      },
      letterSpacing: {
        tightest: "-0.06em",
      },
      fontFamily: {
        display: ["'Cabinet Grotesk'", "'Inter Tight'", "system-ui", "sans-serif"],
        serif: ["'Fraunces'", "Georgia", "serif"],
        body: ["'Satoshi'", "'Inter'", "system-ui", "sans-serif"],
        mono: ["'JetBrains Mono'", "ui-monospace", "monospace"],
      },
      keyframes: {
        marquee: {
          "0%": { transform: "translateX(0)" },
          "100%": { transform: "translateX(-50%)" },
        },
        slidein: {
          "0%": { transform: "translateX(-100%)" },
          "100%": { transform: "translateX(0)" },
        },
        fadein: {
          "0%": { opacity: "0", transform: "translateY(-4px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
      },
      animation: {
        marquee: "marquee 40s linear infinite",
        slidein: "slidein 0.25s ease-out",
        fadein: "fadein 0.15s ease-out",
      },
    },
  },
  plugins: [],
};

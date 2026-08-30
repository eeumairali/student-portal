/** Rebuild CSS after template edits:  npm run css
 *  The built file (static/css/app.css) is committed, so deployment needs no Node. */
module.exports = {
  darkMode: "class",
  content: ["./templates/**/*.html", "./learning/**/*.py"],
  theme: {
    extend: {
      colors: {
        // Structural colors are CSS variables (see input.css :root / .dark) so
        // every bg-paper / text-ink / bg-card / border-line utility already in
        // use across the templates flips automatically — no template changes
        // needed to support dark mode, just toggling the `dark` class on <html>.
        ink: "rgb(var(--c-ink) / <alpha-value>)",
        paper: "rgb(var(--c-paper) / <alpha-value>)",
        card: "rgb(var(--c-card) / <alpha-value>)",
        line: "rgb(var(--c-line) / <alpha-value>)",
        slate: { 500: "rgb(var(--c-slate-500) / <alpha-value>)" },
        teal: { 600: "#0f766e", 700: "#115e56", 50: "#effaf7" },
        mint: { 300: "#7fd8c4", 400: "#4dc4a9", 100: "#d6f2e9" },
      },
      fontFamily: {
        display: ['"Fraunces"', "Georgia", "serif"],
        body: ['"Inter"', "system-ui", "sans-serif"],
        mono: ['"JetBrains Mono"', "ui-monospace", "monospace"],
      },
      boxShadow: { card: "0 1px 2px rgba(18,49,46,.06), 0 8px 24px -16px rgba(18,49,46,.25)" },
    },
  },
  plugins: [],
};

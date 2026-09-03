/** Rebuild CSS after template edits:  npm run css
 *  The built file (static/css/app.css) is committed, so deployment needs no Node. */
module.exports = {
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
        teal: { 600: "#6c63ff", 700: "#554bd8", 50: "#f0efff" },
        mint: { 300: "#9ae7d5", 400: "#58cdb4", 100: "#dcf8f0" },
      },
      fontFamily: {
        display: ['"Fraunces"', "Georgia", "serif"],
        body: ['"Inter"', "system-ui", "sans-serif"],
        mono: ['"JetBrains Mono"', "ui-monospace", "monospace"],
      },
      boxShadow: {
        card: "0 3px 12px rgba(85,75,216,.10), 0 12px 30px -18px rgba(49,43,85,.24)",
        glow: "0 0 0 1px rgba(124,108,255,.25), 0 8px 24px -6px rgba(124,108,255,.35), 0 20px 45px -20px rgba(255,120,170,.30)",
      },
    },
  },
  plugins: [],
};

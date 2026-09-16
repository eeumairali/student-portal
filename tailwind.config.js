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
        // Named "teal"/"mint" for historical reasons — both are CSS variables
        // (see input.css) so a student's chosen color palette (see
        // static/js/site-palette.js) reskins every ring-teal-600 / hover:border-
        // mint-400 utility already in the templates, the same way dark mode does.
        teal: {
          500: "rgb(var(--c-accent-1) / <alpha-value>)",
          600: "rgb(var(--c-accent-1) / <alpha-value>)",
          700: "rgb(var(--c-accent-1-dark) / <alpha-value>)",
          50: "rgb(var(--c-accent-1-tint) / <alpha-value>)",
        },
        mint: {
          100: "rgb(var(--c-accent-2-tint) / <alpha-value>)",
          300: "rgb(var(--c-accent-2-light) / <alpha-value>)",
          400: "rgb(var(--c-accent-2) / <alpha-value>)",
        },
      },
      fontFamily: {
        display: ['"Fraunces"', "Georgia", "serif"],
        body: ['"Inter"', "system-ui", "sans-serif"],
        mono: ['"JetBrains Mono"', "ui-monospace", "monospace"],
      },
      boxShadow: {
        card: "0 2px 10px rgba(102,73,48,.06), 0 12px 28px -18px rgba(102,73,48,.22)",
        glow: "0 0 0 1px rgba(102,73,48,.16), 0 10px 26px -10px rgba(102,73,48,.30)",
      },
    },
  },
  plugins: [],
};

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
        // Named "teal"/"mint" for historical reasons — both now map to the
        // Neutral Elegance brand browns so every ring-teal-600 / hover:border-
        // mint-400 utility already in the templates picks up the new palette.
        teal: { 600: "#664930", 700: "#4d3722", 50: "#FBF3EC" },
        mint: { 300: "#B7A08D", 400: "#997E67", 100: "#F3EAE0" },
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

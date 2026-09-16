/* Applies the student's chosen site-wide color palette (see site-palette.js)
 * to the lesson/notebook page, which has its own separate stylesheet
 * (lesson-theme.css) and CSS variable names (--paper/--ink/--card/--deep)
 * rather than the site's --c-paper/--c-ink/etc. This just maps the same
 * derived palette onto those names. A student's own manual per-lesson color
 * picks (lesson-theme-picker.js, the 🎨 button on this page) still load
 * after this and override whichever of these four they've customized. */
(function () {
  "use strict";

  function tripletToRgb(triplet) {
    return "rgb(" + triplet.split(" ").join(",") + ")";
  }

  function apply() {
    if (!window.SitePalette) return;
    var key = document.documentElement.getAttribute("data-palette-key") || window.SitePalette.current();
    if (!key) return;
    var palette = window.SitePalette.paletteByKey(key);
    if (!palette) return;

    var vars = window.SitePalette.derive(palette.colors);
    var v = window.SitePalette.isDark() ? vars.dark : vars.light;
    var style = document.documentElement.style;
    style.setProperty("--paper", tripletToRgb(v["--c-paper"]));
    style.setProperty("--ink", tripletToRgb(v["--c-ink"]));
    style.setProperty("--card", tripletToRgb(v["--c-card"]));
    style.setProperty("--line", tripletToRgb(v["--c-line"]));
    style.setProperty("--muted", tripletToRgb(v["--c-slate-500"]));
    style.setProperty("--deep", tripletToRgb(v["--c-accent-1"]));
  }

  apply();
})();

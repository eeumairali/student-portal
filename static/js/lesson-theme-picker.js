/* Lets a student pick their own background/text/card/accent colors for the
 * lesson page. Purely cosmetic and per-browser (localStorage) — it doesn't
 * touch the lesson content or anyone else's view of it. */
(function () {
  "use strict";

  var STORAGE_KEY = "lessonTheme";

  function load() {
    try {
      return JSON.parse(localStorage.getItem(STORAGE_KEY) || "{}");
    } catch (e) {
      return {};
    }
  }

  function save(theme) {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(theme));
    } catch (e) { /* ignore (private browsing, storage disabled, etc.) */ }
  }

  function apply(theme) {
    Object.keys(theme).forEach(function (cssVar) {
      if (theme[cssVar]) document.documentElement.style.setProperty(cssVar, theme[cssVar]);
    });
  }

  document.addEventListener("DOMContentLoaded", function () {
    var toggleBtn = document.getElementById("theme-toggle-btn");
    var panel = document.getElementById("theme-picker");
    var resetBtn = document.getElementById("theme-reset-btn");
    if (!toggleBtn || !panel) return;

    var inputs = Array.prototype.slice.call(panel.querySelectorAll("input[type=color]"));
    var theme = load();

    inputs.forEach(function (input) {
      var cssVar = input.dataset.var;
      input.value = theme[cssVar] || input.dataset.default;
      input.addEventListener("input", function () {
        theme[cssVar] = input.value;
        apply(theme);
        save(theme);
      });
    });
    apply(theme);

    toggleBtn.addEventListener("click", function () {
      panel.hidden = !panel.hidden;
    });

    if (resetBtn) {
      resetBtn.addEventListener("click", function () {
        theme = {};
        save(theme);
        inputs.forEach(function (input) {
          input.value = input.dataset.default;
          document.documentElement.style.removeProperty(input.dataset.var);
        });
      });
    }

    document.addEventListener("click", function (e) {
      if (!panel.hidden && !panel.contains(e.target) && e.target !== toggleBtn) {
        panel.hidden = true;
      }
    });
  });
})();

(function () {
  "use strict";
  var KEY = "theme";

  function apply(theme) {
    if (theme === "light") {
      document.documentElement.setAttribute("data-theme", "light");
    } else {
      document.documentElement.removeAttribute("data-theme");
    }
    var meta = document.querySelector('meta[name="color-scheme"]');
    if (meta) meta.setAttribute("content", theme === "light" ? "light" : "dark");
    document.querySelectorAll("[data-theme-toggle]").forEach(function (btn) {
      btn.textContent = theme === "light" ? "Dark mode" : "Light mode";
    });
  }

  function current() {
    try {
      return localStorage.getItem(KEY) || "light";
    } catch (e) {
      return "light";
    }
  }

  apply(current());

  document.addEventListener("click", function (e) {
    var btn = e.target.closest("[data-theme-toggle]");
    if (!btn) return;
    var next = current() === "light" ? "dark" : "light";
    try {
      localStorage.setItem(KEY, next);
    } catch (e) {}
    apply(next);
  });

  document.addEventListener("DOMContentLoaded", function () {
    apply(current());
  });
})();

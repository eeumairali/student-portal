/* Site-wide color palette picker. Every structural color in the portal
 * (ink/paper/card/line/slate/accent-1/accent-2/...) is a CSS variable in RGB
 * triplet form (see input.css), the same mechanism dark mode already uses.
 * A palette here is just 4 brand colors; the rest of the variables are
 * derived from them by hue, so any palette a student picks stays legible
 * (dark-enough text, light-enough backgrounds) without hand-tuning ~15
 * variables x 10 palettes x 2 modes. Selection is per-browser (localStorage),
 * same as dark mode and the lesson-page color picker. */
(function () {
  "use strict";
  var KEY = "sitePalette";

  var PALETTES = [
    { key: "nature", name: "Nature", emoji: "🌿", colors: ["#1B4332", "#2D6A4F", "#95D5B2", "#F8F9FA"] },
    { key: "modern-blue", name: "Modern Blue", emoji: "🔵", colors: ["#03045E", "#0077B6", "#00B4D8", "#CAF0F8"] },
    { key: "ai-purple", name: "AI Purple", emoji: "🟣", colors: ["#240046", "#5A189A", "#9D4EDD", "#E0AAFF"] },
    { key: "teal", name: "Teal", emoji: "🌊", colors: ["#003049", "#007F86", "#00B4A2", "#E8F8F5"] },
    { key: "dark-tech", name: "Dark Tech", emoji: "🌙", colors: ["#0B132B", "#1C2541", "#3A506B", "#5BC0BE"] },
    { key: "green", name: "Green", emoji: "🍃", colors: ["#132A13", "#31572C", "#4F772D", "#90A955"] },
    { key: "warm-modern", name: "Warm Modern", emoji: "🧡", colors: ["#264653", "#2A9D8F", "#E9C46A", "#F4A261"] },
    { key: "pastel", name: "Pastel", emoji: "🎨", colors: ["#A8E6CF", "#DCEDC1", "#FFD3B6", "#FFAAA5"] },
    { key: "elegant", name: "Elegant", emoji: "☕", colors: ["#F0ECE3", "#DFD3C3", "#C7B198", "#596E79"] },
    { key: "soft-creative", name: "Soft Creative", emoji: "🌸", colors: ["#ECA3F5", "#FDBAF8", "#B0EFEB", "#EDFFA9"] },
    { key: "rainbow", name: "Rainbow", emoji: "🌈", colors: ["#FF6B6B", "#FFD93D", "#6BCB77", "#4D96FF"] },
    { key: "candy", name: "Candy", emoji: "🍭", colors: ["#FF6FB1", "#FFD34E", "#4DB6FF", "#7ED957"] },
    { key: "unicorn", name: "Unicorn", emoji: "🦄", colors: ["#FFB3E6", "#CDB4FF", "#A2D2FF", "#B9FBC0"] },
    { key: "bubblegum", name: "Bubblegum", emoji: "🍬", colors: ["#FF85A1", "#FFB2E6", "#B28DFF", "#70D6FF"] },
    { key: "sunshine", name: "Sunshine", emoji: "☀️", colors: ["#FFD93D", "#FF9F1C", "#FF6B6B", "#FFF3B0"] },
    { key: "art-class", name: "Art Class", emoji: "🎨", colors: ["#FFADAD", "#FFD6A5", "#FDFFB6", "#CAFFBF"] },
    { key: "toy-box", name: "Toy Box", emoji: "🧸", colors: ["#FF595E", "#FFCA3A", "#8AC926", "#1982C4"] },
    { key: "dino", name: "Dino", emoji: "🦖", colors: ["#8AC926", "#52B788", "#FFD166", "#F9844A"] },
    { key: "mermaid", name: "Mermaid", emoji: "🧜", colors: ["#00B4D8", "#90E0EF", "#C77DFF", "#FF99C8"] },
    { key: "space", name: "Space", emoji: "🚀", colors: ["#3A0CA3", "#4361EE", "#4CC9F0", "#F72585"] },
    { key: "watermelon", name: "Watermelon", emoji: "🍉", colors: ["#FF5D8F", "#FF8FA3", "#80ED99", "#57CC99"] },
    { key: "ice-cream", name: "Ice Cream", emoji: "🍦", colors: ["#FFC8DD", "#FFAFCC", "#BDE0FE", "#A2D2FF"] },
    { key: "balloon", name: "Balloon", emoji: "🎈", colors: ["#FF595E", "#FFCA3A", "#6A4C93", "#4D96FF"] },
    { key: "flower", name: "Flower", emoji: "🌸", colors: ["#FF8FAB", "#FFC2D1", "#FFE066", "#70E000"] },
    { key: "ocean", name: "Ocean", emoji: "🌊", colors: ["#00B4D8", "#48CAE4", "#90E0EF", "#0077B6"] },
    { key: "bumblebee", name: "Bumblebee", emoji: "🐝", colors: ["#FFD60A", "#FFC300", "#FF8500", "#FFF3B0"] },
    { key: "peachy", name: "Peachy", emoji: "🍑", colors: ["#FFB5A7", "#FCD5CE", "#F8EDEB", "#F9DCC4"] },
    { key: "frog", name: "Frog", emoji: "🐸", colors: ["#70E000", "#38B000", "#FFD60A", "#9EF01A"] },
    { key: "neon-fun", name: "Neon Fun", emoji: "🎮", colors: ["#F72585", "#7209B7", "#4CC9F0", "#B9F227"] },
    { key: "cupcake", name: "Cupcake", emoji: "🧁", colors: ["#FFAFCC", "#FFC8DD", "#CDB4DB", "#BDE0FE"] },
  ];

  // ---- color math -----------------------------------------------------
  function hexToHsl(hex) {
    var r = parseInt(hex.slice(1, 3), 16) / 255;
    var g = parseInt(hex.slice(3, 5), 16) / 255;
    var b = parseInt(hex.slice(5, 7), 16) / 255;
    var max = Math.max(r, g, b), min = Math.min(r, g, b);
    var h = 0, s = 0, l = (max + min) / 2;
    var d = max - min;
    if (d !== 0) {
      s = d / (1 - Math.abs(2 * l - 1));
      switch (max) {
        case r: h = ((g - b) / d) % 6; break;
        case g: h = (b - r) / d + 2; break;
        default: h = (r - g) / d + 4;
      }
      h *= 60;
      if (h < 0) h += 360;
    }
    return { h: h, s: s * 100, l: l * 100 };
  }

  function hslToRgbTriplet(h, s, l) {
    s = Math.max(0, Math.min(100, s)) / 100;
    l = Math.max(0, Math.min(100, l)) / 100;
    var c = (1 - Math.abs(2 * l - 1)) * s;
    var x = c * (1 - Math.abs(((h / 60) % 2) - 1));
    var m = l - c / 2;
    var r, g, b;
    if (h < 60) { r = c; g = x; b = 0; }
    else if (h < 120) { r = x; g = c; b = 0; }
    else if (h < 180) { r = 0; g = c; b = x; }
    else if (h < 240) { r = 0; g = x; b = c; }
    else if (h < 300) { r = x; g = 0; b = c; }
    else { r = c; g = 0; b = x; }
    var toByte = function (v) { return Math.round((v + m) * 255); };
    return toByte(r) + " " + toByte(g) + " " + toByte(b);
  }

  function clampSat(s, max) { return Math.min(s, max); }
  function floorSat(s, min) { return Math.max(s, min); }

  // Derive every structural CSS variable from a palette's 4 brand colors,
  // for both light and dark mode. Roles keep a fixed lightness target (so
  // text stays legible and backgrounds stay light) but take their hue from
  // the palette, so each preset still reads as visually distinct.
  function derive(colors) {
    var hsl = colors.map(hexToHsl).sort(function (a, b) { return b.l - a.l; });
    var lightest = hsl[0], midLight = hsl[1], midDark = hsl[2], darkest = hsl[3];

    var light = {
      "--c-ink": hslToRgbTriplet(darkest.h, clampSat(darkest.s, 45), 16),
      "--c-paper": hslToRgbTriplet(lightest.h, clampSat(lightest.s, 25), 97),
      "--c-card": hslToRgbTriplet(lightest.h, clampSat(lightest.s, 35), 93),
      "--c-line": hslToRgbTriplet(midDark.h, clampSat(midDark.s, 30), 84),
      "--c-slate-500": hslToRgbTriplet(midDark.h, clampSat(midDark.s, 20), 42),
      "--c-accent-1": hslToRgbTriplet(midDark.h, floorSat(midDark.s, 55), 38),
      "--c-accent-1-dark": hslToRgbTriplet(midDark.h, floorSat(midDark.s, 55), 30),
      "--c-accent-1-tint": hslToRgbTriplet(midDark.h, clampSat(midDark.s, 30), 96),
      "--c-accent-2": hslToRgbTriplet(midLight.h, floorSat(midLight.s, 45), 55),
      "--c-accent-2-light": hslToRgbTriplet(midLight.h, floorSat(midLight.s, 45), 66),
      "--c-accent-2-tint": hslToRgbTriplet(midLight.h, clampSat(midLight.s, 35), 92),
      "--c-accent-3": hslToRgbTriplet(lightest.h, clampSat(lightest.s, 25), 88),
      "--c-peach": hslToRgbTriplet(midLight.h, 55, 82),
    };
    light["--c-glow"] = light["--c-accent-1"];

    var dark = {
      "--c-ink": hslToRgbTriplet(midLight.h, clampSat(midLight.s, 15), 92),
      "--c-paper": hslToRgbTriplet(darkest.h, clampSat(darkest.s, 35), 8),
      "--c-card": hslToRgbTriplet(darkest.h, clampSat(darkest.s, 30), 12),
      "--c-line": hslToRgbTriplet(midDark.h, clampSat(midDark.s, 30), 24),
      "--c-slate-500": hslToRgbTriplet(midLight.h, clampSat(midLight.s, 15), 68),
      "--c-accent-1": hslToRgbTriplet(midDark.h, floorSat(midDark.s, 40), 68),
      "--c-accent-1-dark": hslToRgbTriplet(midDark.h, floorSat(midDark.s, 40), 78),
      "--c-accent-1-tint": hslToRgbTriplet(midDark.h, clampSat(midDark.s, 30), 14),
      "--c-accent-2": hslToRgbTriplet(midLight.h, floorSat(midLight.s, 35), 55),
      "--c-accent-2-light": hslToRgbTriplet(midLight.h, floorSat(midLight.s, 35), 63),
      "--c-accent-2-tint": hslToRgbTriplet(midLight.h, clampSat(midLight.s, 30), 14),
      "--c-accent-3": hslToRgbTriplet(darkest.h, clampSat(darkest.s, 25), 26),
      "--c-peach": hslToRgbTriplet(midLight.h, 35, 30),
    };
    dark["--c-glow"] = dark["--c-accent-1"];

    return { light: light, dark: dark };
  }

  function isDark() {
    return document.documentElement.getAttribute("data-theme") === "dark";
  }

  function current() {
    try {
      return localStorage.getItem(KEY) || "";
    } catch (e) {
      return "";
    }
  }

  function paletteByKey(key) {
    for (var i = 0; i < PALETTES.length; i++) {
      if (PALETTES[i].key === key) return PALETTES[i];
    }
    return null;
  }

  function applyVars(vars) {
    var style = document.documentElement.style;
    Object.keys(vars).forEach(function (name) { style.setProperty(name, vars[name]); });
  }

  function clearVars(vars) {
    var style = document.documentElement.style;
    Object.keys(vars).forEach(function (name) { style.removeProperty(name); });
  }

  var ALL_VAR_NAMES = [
    "--c-ink", "--c-paper", "--c-card", "--c-line", "--c-slate-500",
    "--c-accent-1", "--c-accent-1-dark", "--c-accent-1-tint",
    "--c-accent-2", "--c-accent-2-light", "--c-accent-2-tint",
    "--c-accent-3", "--c-peach", "--c-glow",
  ];

  function reapply() {
    var key = current();
    var palette = key && paletteByKey(key);
    if (!palette) {
      clearVars(ALL_VAR_NAMES.reduce(function (o, n) { o[n] = true; return o; }, {}));
      return;
    }
    var vars = derive(palette.colors);
    applyVars(isDark() ? vars.dark : vars.light);
  }

  function getCookie(name) {
    var match = document.cookie.match("(^|;\\s*)" + name + "=([^;]*)");
    return match ? decodeURIComponent(match[2]) : "";
  }

  function persistToServer(key) {
    var csrftoken = getCookie("csrftoken");
    if (!csrftoken) return;
    fetch("/accounts/theme-palette/", {
      method: "POST",
      credentials: "same-origin",
      headers: { "Content-Type": "application/json", "X-CSRFToken": csrftoken },
      body: JSON.stringify({ key: key }),
    }).catch(function () { /* per-browser localStorage already has it; sync can retry next visit */ });
  }

  function select(key) {
    try {
      if (key) localStorage.setItem(KEY, key);
      else localStorage.removeItem(KEY);
    } catch (e) { /* ignore */ }
    reapply();
    persistToServer(key);
  }

  // Apply immediately (this script is loaded blocking, before <body>, same
  // as theme-toggle.js) so there's no flash of the default palette.
  reapply();

  window.SitePalette = {
    PALETTES: PALETTES, current: current, select: select, reapply: reapply,
    derive: derive, paletteByKey: paletteByKey, isDark: isDark,
  };

  document.addEventListener("DOMContentLoaded", function () {
    var toggleBtns = Array.prototype.slice.call(document.querySelectorAll(".palette-trigger"));
    var panel = document.getElementById("palette-picker");
    var grid = document.getElementById("palette-grid");
    var resetBtn = document.getElementById("palette-reset-btn");
    if (!toggleBtns.length || !panel || !grid) return;

    function setOpen(isOpen) {
      panel.hidden = !isOpen;
      panel.classList.toggle("is-open", isOpen);
      toggleBtns.forEach(function (btn) {
        btn.setAttribute("aria-expanded", String(isOpen));
      });
    }

    setOpen(false);

    PALETTES.forEach(function (p) {
      var btn = document.createElement("button");
      btn.type = "button";
      btn.className = "palette-swatch";
      btn.setAttribute("data-key", p.key);
      btn.title = p.name;
      var dots = document.createElement("span");
      dots.className = "palette-dots";
      p.colors.forEach(function (c) {
        var dot = document.createElement("span");
        dot.className = "palette-dot";
        dot.style.background = c;
        dots.appendChild(dot);
      });
      var label = document.createElement("span");
      label.className = "palette-name";
      label.textContent = p.emoji + " " + p.name;
      btn.appendChild(dots);
      btn.appendChild(label);
      btn.addEventListener("click", function () {
        select(p.key);
        markActive();
      });
      grid.appendChild(btn);
    });

    function markActive() {
      var active = current();
      grid.querySelectorAll(".palette-swatch").forEach(function (btn) {
        btn.classList.toggle("is-active", btn.getAttribute("data-key") === active);
      });
      if (resetBtn) resetBtn.classList.toggle("is-active", !active);
    }
    markActive();

    toggleBtns.forEach(function (btn) {
      btn.addEventListener("click", function () {
        setOpen(!panel.classList.contains("is-open"));
      });
    });

    if (resetBtn) {
      resetBtn.addEventListener("click", function () {
        select("");
        markActive();
      });
    }

    document.addEventListener("click", function (e) {
      if (panel.hidden) return;
      var onTrigger = toggleBtns.some(function (btn) { return btn === e.target || btn.contains(e.target); });
      if (!onTrigger && !panel.contains(e.target)) setOpen(false);
    });
  });
})();

/* Small motion layer for the logged-in pages: count-up numbers, animated
 * progress bars, staggered entrance of cards and list rows, and coloured
 * initial avatars. Everything is progressive: without JS the page is complete. */
(function () {
  "use strict";
  var reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  // Numbers like "16", "285", "90%", "81 / 90", "16/21" inside cards.
  var NUM = /^\s*(\d[\d,]*)(\s*\/\s*\d[\d,]*)?\s*(%?)\s*$/;

  function countUp(el) {
    var m = el.textContent.match(NUM);
    if (!m) return;
    var target = parseInt(m[1].replace(/,/g, ""), 10);
    if (!target) return;
    var rest = (m[2] || "") + m[3];
    var start = null, dur = Math.min(1400, 500 + target * 8);
    function frame(t) {
      if (start === null) start = t;
      var p = Math.min(1, (t - start) / dur);
      var eased = 1 - Math.pow(1 - p, 3);
      el.textContent = Math.round(target * eased).toLocaleString() + rest;
      if (p < 1) requestAnimationFrame(frame);
    }
    el.textContent = "0" + rest;
    requestAnimationFrame(frame);
  }

  function avatarColour(name) {
    var h = 0;
    for (var i = 0; i < name.length; i++) h = (h * 31 + name.charCodeAt(i)) % 360;
    return "hsl(" + h + " 62% 46%)";
  }

  function init() {
    document.querySelectorAll("[data-avatar]").forEach(function (el) {
      el.style.background = avatarColour(el.getAttribute("data-avatar") || "?");
    });

    if (reduce) return;

    var main = document.getElementById("main");
    if (!main || main.querySelector(".landing-page")) return; // landing has its own motion

    // Count-up numbers.
    main.querySelectorAll(".card .font-display, .card .text-2xl, .card .text-3xl, [data-count]").forEach(function (el) {
      if (el.children.length === 0 && NUM.test(el.textContent)) countUp(el);
    });

    // Progress bars: inline width % on a rounded bar fills from zero.
    main.querySelectorAll('[style*="width"]').forEach(function (bar) {
      var w = bar.style.width;
      if (!/%$/.test(w) || !bar.parentElement || !/rounded-full/.test(bar.className + bar.parentElement.className)) return;
      bar.style.width = "0%";
      bar.style.transition = "width 1.1s cubic-bezier(.22,1,.36,1)";
      requestAnimationFrame(function () { requestAnimationFrame(function () { bar.style.width = w; }); });
    });

    // Staggered entrance for top-level blocks, cards and list rows.
    var items = [];
    Array.prototype.forEach.call(main.children, function (el) { items.push(el); });
    main.querySelectorAll(".divide-y > *, .grid > .card").forEach(function (el) { items.push(el); });
    items.forEach(function (el, i) {
      el.classList.add("motion-in");
      el.style.animationDelay = Math.min(i * 35, 700) + "ms";
    });
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", init);
  else init();
}());

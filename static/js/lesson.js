/* Lesson document interactivity: progress bar, mark-done, and timed
 * solution reveals — saved to the server when the viewer is the lesson's
 * own student (data-can-edit="1"). In a database-free preview,
 * data-lesson-id is empty and nothing hits the network — the page still
 * works, it just doesn't persist. Practice code runs on the student's own
 * computer, never in the browser or on the server. */
(function () {
  "use strict";

  var DEFAULT_HINT_SECONDS = 20;

  function getCookie(name) {
    var match = document.cookie.match("(^|;\\s*)" + name + "=([^;]*)");
    return match ? decodeURIComponent(match[2]) : null;
  }

  document.addEventListener("DOMContentLoaded", function () {
    var root = document.getElementById("lesson-root");
    var lessonId = root ? root.dataset.lessonId : "";
    var canEdit = !!(root && root.dataset.canEdit === "1" && lessonId);
    var csrftoken = getCookie("csrftoken");

    var practices = Array.prototype.slice.call(document.querySelectorAll(".practice[data-task-id]"));
    var fill = document.getElementById("lesson-fill");
    var count = document.getElementById("lesson-count");
    var doneMsg = document.getElementById("lesson-donemsg");
    var total = practices.length;

    function post(path, body) {
      if (!canEdit) return Promise.resolve();
      return fetch(path, {
        method: "POST",
        headers: { "Content-Type": "application/json", "X-CSRFToken": csrftoken },
        credentials: "same-origin",
        body: JSON.stringify(body),
      });
    }

    function refresh() {
      var n = document.querySelectorAll(".practice.done").length;
      if (fill) fill.style.width = (total ? (n / total * 100) : 0) + "%";
      if (count) count.textContent = n + " / " + total;
      if (doneMsg) doneMsg.classList.toggle("show", total > 0 && n === total);
    }

    function markDone(practice, done, save) {
      practice.classList.toggle("done", done);
      var dbtn = practice.querySelector(".dbtn");
      if (dbtn) dbtn.textContent = done ? "Done" : "Mark done";
      refresh();
      if (save !== false) {
        post("/lesson/" + lessonId + "/task/" + practice.dataset.taskId + "/complete/", { complete: done });
      }
    }

    // ---- hydrate saved state ----
    var stateEl = document.getElementById("lesson-state");
    var state = { completed: [] };
    if (stateEl) {
      try { state = JSON.parse(stateEl.textContent); } catch (e) { /* ignore */ }
    }
    (state.completed || []).forEach(function (taskId) {
      var practice = document.querySelector('.practice[data-task-id="' + CSS.escape(taskId) + '"]');
      if (practice) markDone(practice, true, false);
    });

    // ---- mark-done + timed solution reveal ----
    practices.forEach(function (practice) {
      var dbtn = practice.querySelector(".dbtn");
      if (dbtn) {
        dbtn.addEventListener("click", function () {
          markDone(practice, !practice.classList.contains("done"));
        });
      }

      if (practice.dataset.hasSolution !== "1") return;

      var hbtn = practice.querySelector(".hbtn");
      var hint = practice.querySelector(".hint");
      var row = practice.querySelector(".practice-actions");
      if (!hbtn || !hint || !row) return;

      var holdSeconds = parseInt(practice.dataset.hintSeconds, 10);
      if (isNaN(holdSeconds) || holdSeconds < 0) holdSeconds = DEFAULT_HINT_SECONDS;

      function reveal() {
        hint.classList.add("show");
        hint.scrollIntoView({ behavior: "smooth", block: "nearest" });
        post("/lesson/" + lessonId + "/task/" + practice.dataset.taskId + "/reveal/", {});
      }

      hbtn.addEventListener("click", function () {
        if (hbtn.disabled) return;
        hbtn.disabled = true;
        hbtn.style.display = "none";

        if (holdSeconds === 0) {
          reveal();
          return;
        }

        var timer = document.createElement("div");
        timer.className = "timer";
        var ring = document.createElement("div");
        ring.className = "ring";
        var label = document.createElement("span");
        timer.appendChild(ring);
        timer.appendChild(label);
        row.insertBefore(timer, dbtn);

        var left = holdSeconds;
        var tick = function () {
          var m = Math.floor(left / 60), s = left % 60;
          label.textContent = "Answer in " + m + ":" + String(s).padStart(2, "0");
          ring.style.background = "conic-gradient(var(--amber) " + ((holdSeconds - left) / holdSeconds * 360) + "deg,var(--amberbg) 0deg)";
          if (left <= 0) {
            clearInterval(iv);
            timer.remove();
            reveal();
            return;
          }
          left--;
        };
        tick();
        var iv = setInterval(tick, 1000);
      });
    });

    // ---- copy-code buttons on every code block ----
    document.querySelectorAll(".lesson-doc pre").forEach(function (pre) {
      if (pre.closest(".code-block")) return;
      var wrap = document.createElement("div");
      wrap.className = "code-block";
      pre.parentNode.insertBefore(wrap, pre);
      wrap.appendChild(pre);

      var btn = document.createElement("button");
      btn.type = "button";
      btn.className = "copy-btn";
      btn.textContent = "Copy";
      wrap.appendChild(btn);

      btn.addEventListener("click", function () {
        navigator.clipboard.writeText(pre.textContent).then(function () {
          btn.textContent = "Copied";
          btn.classList.add("copied");
          setTimeout(function () {
            btn.textContent = "Copy";
            btn.classList.remove("copied");
          }, 1500);
        });
      });
    });

    // ---- quiz options: ungraded, click any option to see its feedback ----
    document.querySelectorAll(".quiz-option").forEach(function (btn) {
      btn.addEventListener("click", function () {
        btn.classList.add("picked");
        btn.classList.toggle("correct", btn.dataset.correct === "1");
        btn.classList.toggle("incorrect", btn.dataset.correct !== "1");
        var wrap = btn.closest(".quiz-option-wrap");
        var feedback = wrap && wrap.querySelector(".quiz-feedback");
        if (feedback) feedback.classList.add("show");
      });
    });

    // ---- checklist: self-check only, not saved to the server ----
    document.querySelectorAll(".checklist-check").forEach(function (btn) {
      btn.addEventListener("click", function () {
        var pressed = btn.getAttribute("aria-pressed") === "true";
        btn.setAttribute("aria-pressed", String(!pressed));
        btn.closest(".checklist-item").classList.toggle("done", !pressed);
      });
    });

    refresh();
  });
})();

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

    // ---- gentle nudge: scrolled past an unmarked step ----
    if (total > 0 && "IntersectionObserver" in window) {
      var stack = document.createElement("div");
      stack.className = "nudge-stack";
      document.body.appendChild(stack);
      var nudged = {};

      function showNudge(practice) {
        var taskId = practice.dataset.taskId;
        if (nudged[taskId] || practice.classList.contains("done")) return;
        nudged[taskId] = true;

        var index = practice.querySelector(".practice-num");
        var label = index ? index.textContent : "";

        var card = document.createElement("div");
        card.className = "nudge";
        card.innerHTML =
          '<p class="nudge-text">Understood step ' + label + ' of ' + total + '?</p>' +
          '<div class="nudge-actions">' +
          '<button type="button" class="nudge-yes">Yes, mark done</button>' +
          '<button type="button" class="nudge-no">Not yet</button>' +
          "</div>";
        stack.appendChild(card);
        requestAnimationFrame(function () { card.classList.add("show"); });

        function remove() {
          card.classList.remove("show");
          setTimeout(function () { card.remove(); }, 200);
        }
        card.querySelector(".nudge-yes").addEventListener("click", function () {
          markDone(practice, true);
          remove();
        });
        card.querySelector(".nudge-no").addEventListener("click", remove);
        setTimeout(remove, 12000);
      }

      var observer = new IntersectionObserver(function (entries) {
        entries.forEach(function (entry) {
          if (!entry.isIntersecting && entry.boundingClientRect.top < 0) {
            showNudge(entry.target);
          }
        });
      }, { threshold: 0 });
      practices.forEach(function (p) { observer.observe(p); });
    }

    // ---- copy-code buttons on every code block ----
    document.querySelectorAll(".lesson-doc pre").forEach(function (pre) {
      if (pre.closest(".code-block")) return;
      if (pre.closest(".example-protect")) return;
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

    // ---- protected examples: no select, no copy, no right-click ----
    document.querySelectorAll(".example-protect pre").forEach(function (pre) {
      pre.addEventListener("copy", function (e) { e.preventDefault(); });
      pre.addEventListener("contextmenu", function (e) { e.preventDefault(); });
      pre.addEventListener("dragstart", function (e) { e.preventDefault(); });
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

    // ---- solution lock: passcode-gated full code dump ----
    document.querySelectorAll("[data-solution-lock]").forEach(function (lock) {
      var solutionId = lock.dataset.solutionId;
      var form = lock.querySelector("[data-solution-form]");
      var input = lock.querySelector("[data-solution-input]");
      var error = lock.querySelector("[data-solution-error]");
      var prompt = lock.querySelector("[data-solution-prompt]");
      var body = lock.querySelector("[data-solution-body]");
      if (!form || !lessonId) return;

      form.addEventListener("submit", function (e) {
        e.preventDefault();
        error.hidden = true;
        var submitBtn = form.querySelector("button");
        submitBtn.disabled = true;

        fetch("/lesson/" + lessonId + "/solution/" + encodeURIComponent(solutionId) + "/unlock/", {
          method: "POST",
          headers: { "Content-Type": "application/json", "X-CSRFToken": csrftoken },
          credentials: "same-origin",
          body: JSON.stringify({ passcode: input.value }),
        })
          .then(function (res) { return res.json().then(function (data) { return { ok: res.ok, data: data }; }); })
          .then(function (result) {
            submitBtn.disabled = false;
            if (!result.ok || !result.data.ok) {
              error.textContent = (result.data && result.data.error) || "Incorrect passcode.";
              error.hidden = false;
              input.value = "";
              input.focus();
              return;
            }
            body.innerHTML = result.data.html;
            body.hidden = false;
            prompt.remove();
            body.querySelectorAll("pre").forEach(function (pre) {
              pre.addEventListener("copy", function (ev) { ev.preventDefault(); });
              pre.addEventListener("contextmenu", function (ev) { ev.preventDefault(); });
              pre.addEventListener("dragstart", function (ev) { ev.preventDefault(); });
            });
          })
          .catch(function () {
            submitBtn.disabled = false;
            error.textContent = "Something went wrong — try again.";
            error.hidden = false;
          });
      });
    });

    // ---- standalone links (a paragraph that's just [name](url)) become
    // resource buttons — used for "notebook on Google Drive" style links ----
    document.querySelectorAll(".lesson-doc p").forEach(function (p) {
      var onlyChild = p.childNodes.length === 1 ? p.childNodes[0] : null;
      if (onlyChild && onlyChild.tagName === "A") {
        p.classList.add("resource-link-wrap");
        onlyChild.classList.add("resource-link");
        onlyChild.target = "_blank";
        onlyChild.rel = "noopener noreferrer";
      }
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

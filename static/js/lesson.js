/* Lesson document interactivity: progress bar, timed hints, choice tasks,
 * mark-done, checklist, and saving blanks/completions/reveals to the server
 * when the viewer is the lesson's own student (data-can-edit="1"). In a
 * database-free preview, data-lesson-id is empty and nothing hits the
 * network — the page still works, it just doesn't persist. */
(function () {
  "use strict";

  var DEFAULT_HINT_SECONDS = 30;

  function getCookie(name) {
    var match = document.cookie.match("(^|;\\s*)" + name + "=([^;]*)");
    return match ? decodeURIComponent(match[2]) : null;
  }

  document.addEventListener("DOMContentLoaded", function () {
    var root = document.getElementById("lesson-root");
    var lessonId = root ? root.dataset.lessonId : "";
    var canEdit = !!(root && root.dataset.canEdit === "1" && lessonId);
    var csrftoken = getCookie("csrftoken");

    var tasks = Array.prototype.slice.call(document.querySelectorAll(".task[data-task-id]"));
    var fill = document.getElementById("lesson-fill");
    var count = document.getElementById("lesson-count");
    var doneMsg = document.getElementById("lesson-donemsg");
    var total = tasks.length;

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
      var n = document.querySelectorAll(".task.done").length;
      if (fill) fill.style.width = (total ? (n / total * 100) : 0) + "%";
      if (count) count.textContent = n + " / " + total;
      if (doneMsg) doneMsg.classList.toggle("show", total > 0 && n === total);
    }

    function markDone(task, done, save) {
      task.classList.toggle("done", done);
      var dbtn = task.querySelector(".dbtn");
      if (dbtn) dbtn.textContent = done ? "Done" : "Mark done";
      refresh();
      if (save !== false) {
        post("/lesson/" + lessonId + "/task/" + task.dataset.taskId + "/complete/", { complete: done });
      }
    }

    // ---- hydrate saved state ----
    var stateEl = document.getElementById("lesson-state");
    var state = { answers: {}, completed: [], checked: [] };
    if (stateEl) {
      try { state = JSON.parse(stateEl.textContent); } catch (e) { /* ignore */ }
    }
    document.querySelectorAll(".blank[data-blank-id]").forEach(function (el) {
      var v = state.answers[el.dataset.blankId];
      if (v !== undefined) el.value = v;
    });
    (state.completed || []).forEach(function (taskId) {
      var task = document.querySelector('.task[data-task-id="' + CSS.escape(taskId) + '"]');
      if (task) markDone(task, true, false);
    });
    (state.checked || []).forEach(function (checkId) {
      var box = document.getElementById(checkId);
      if (box) {
        box.checked = true;
        var label = document.querySelector('label[for="' + checkId + '"]');
        if (label) label.classList.add("checked");
      }
    });

    // ---- blanks: save on blur and on a debounce while typing ----
    var saveTimers = {};
    function saveBlank(el) {
      var id = el.dataset.blankId;
      var savedTag = el.parentElement.querySelector(".save-state[data-for='" + id + "']");
      post("/lesson/" + lessonId + "/answer/", { blank_id: id, value: el.value }).then(function (resp) {
        if (resp && resp.ok && savedTag) {
          savedTag.classList.add("show");
          clearTimeout(savedTag._hideTimer);
          savedTag._hideTimer = setTimeout(function () { savedTag.classList.remove("show"); }, 1500);
        }
      });
    }
    document.querySelectorAll(".blank[data-blank-id]").forEach(function (el) {
      if (!canEdit) { el.disabled = true; return; }
      var tag = document.createElement("span");
      tag.className = "save-state";
      tag.dataset.for = el.dataset.blankId;
      tag.textContent = "Saved";
      el.insertAdjacentElement("afterend", tag);

      el.addEventListener("blur", function () { saveBlank(el); });
      el.addEventListener("input", function () {
        clearTimeout(saveTimers[el.dataset.blankId]);
        saveTimers[el.dataset.blankId] = setTimeout(function () { saveBlank(el); }, 900);
      });
    });

    // ---- choice tasks: instant feedback, self-completing ----
    tasks.filter(function (t) { return t.dataset.type === "choice"; }).forEach(function (task) {
      var why = task.querySelector(".why");
      var opts = Array.prototype.slice.call(task.querySelectorAll(".opt"));
      opts.forEach(function (opt) {
        opt.addEventListener("click", function () {
          var ok = opt.dataset.correct === "1";
          if (ok) {
            opts.forEach(function (o) { if (o.dataset.correct !== "1") o.classList.add("wrong"); });
            opt.classList.add("right");
            if (why) {
              why.className = "why show ok";
              why.textContent = opt.dataset.feedback || "Correct.";
            }
            markDone(task, true);
          } else {
            opt.classList.add("wrong");
            if (why) {
              why.className = "why show no";
              why.textContent = opt.dataset.feedback || "Not quite — try again.";
            }
          }
        });
      });
    });

    // ---- everything else: mark-done button, optional timed hint ----
    tasks.filter(function (t) { return t.dataset.type !== "choice"; }).forEach(function (task) {
      var dbtn = task.querySelector(".dbtn");
      if (dbtn) {
        dbtn.addEventListener("click", function () {
          markDone(task, !task.classList.contains("done"));
        });
      }

      if (task.dataset.hasSolution !== "1") return;

      var hbtn = task.querySelector(".hbtn");
      var hint = task.querySelector(".hint");
      var row = task.querySelector(".hintrow");
      if (!hbtn || !hint || !row) return;

      var holdSeconds = parseInt(task.dataset.hintSeconds, 10);
      if (isNaN(holdSeconds) || holdSeconds < 0) holdSeconds = DEFAULT_HINT_SECONDS;

      function reveal() {
        hint.classList.add("show");
        hint.scrollIntoView({ behavior: "smooth", block: "nearest" });
        post("/lesson/" + lessonId + "/task/" + task.dataset.taskId + "/reveal/", {});
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
          label.textContent = "Keep trying — answer in " + m + ":" + String(s).padStart(2, "0");
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

    // ---- checklist ----
    document.querySelectorAll(".checklist input[type=checkbox]").forEach(function (box) {
      if (!canEdit) { box.disabled = true; }
      box.addEventListener("change", function () {
        var label = document.querySelector('label[for="' + box.id + '"]');
        if (label) label.classList.toggle("checked", box.checked);
        post("/lesson/" + lessonId + "/check/" + box.dataset.checkId + "/", { checked: box.checked });
      });
    });

    refresh();
  });
})();

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
      updateTaskLocks();
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

    // ---- code practice: browser-local Python, output checks, and unlocks ----
    // Pyodide runs inside the learner's browser. Their code is never sent to
    // Django or executed on the portal server.
    var pyodidePromise = null;
    function getPyodide() {
      if (!window.loadPyodide) return Promise.reject(new Error("The Python runner could not load. Check your connection and refresh."));
      if (!pyodidePromise) pyodidePromise = window.loadPyodide({ indexURL: "https://cdn.jsdelivr.net/pyodide/v0.27.7/full/" });
      return pyodidePromise;
    }
    function packagesUsedBy(code) {
      // These packages are part of Pyodide's published package set. Loading
      // them here is browser-local: no pip install and no server access.
      var packageNames = {
        numpy: "numpy", pandas: "pandas", matplotlib: "matplotlib",
        scipy: "scipy", sklearn: "scikit-learn", statsmodels: "statsmodels",
        networkx: "networkx"
      };
      var used = {};
      var re = /^\s*(?:from|import)\s+([A-Za-z_][A-Za-z0-9_]*)/gm;
      var match;
      while ((match = re.exec(code)) !== null) {
        var packageName = packageNames[match[1]];
        if (packageName) used[packageName] = true;
      }
      return Object.keys(used);
    }
    function normaliseOutput(value) {
      return String(value || "").replace(/\r\n/g, "\n").split("\n").map(function (line) { return line.replace(/\s+$/g, ""); }).join("\n").trim();
    }
    function showResult(task, message, ok) {
      var result = task.querySelector(".code-result");
      if (!result) return;
      result.textContent = message;
      result.className = "code-result show " + (ok ? "ok" : "no");
    }
    function startSelfPracticeTimer(task) {
      if (task.dataset.timerStarted === "1" || task.dataset.practiceKind !== "self") return;
      task.dataset.timerStarted = "1";
      var label = task.querySelector(".practice-timer");
      var seconds = parseInt(task.dataset.practiceSeconds, 10);
      if (isNaN(seconds) || seconds < 1) seconds = 60;
      var left = seconds;
      function tick() {
        if (task.classList.contains("done")) return;
        var m = Math.floor(left / 60), s = left % 60;
        if (label) label.textContent = "Time remaining: " + m + ":" + String(s).padStart(2, "0");
        if (left <= 0) {
          if (label) label.textContent = "Time is up — you can still submit, retry, or ask for a hint.";
          showResult(task, "Time is up. Keep going and submit your own code when ready.", false);
          return;
        }
        left--;
        setTimeout(tick, 1000);
      }
      tick();
    }
    function updateTaskLocks() {
      var waiting = false;
      tasks.forEach(function (task) {
        var available = !waiting;
        task.classList.toggle("locked", !available);
        task.querySelectorAll("button, textarea").forEach(function (control) { control.disabled = !available; });
        if (available) startSelfPracticeTimer(task);
        if (!task.classList.contains("done")) waiting = true;
      });
    }
    tasks.filter(function (task) { return task.dataset.type === "code"; }).forEach(function (task) {
      var editor = task.querySelector(".code-editor");
      var runButton = task.querySelector(".runbtn");
      var resetButton = task.querySelector(".resetbtn");
      var checkButton = task.querySelector(".checkbtn");
      var consoleEl = task.querySelector(".console");
      var practice = task.querySelector(".code-practice");
      var starter = editor ? editor.value : "";
      var lastOutput = null;

      function runCode() {
        if (!editor || !consoleEl) return Promise.resolve(null);
        runButton.disabled = true;
        consoleEl.textContent = "Running…";
        return getPyodide().then(function (pyodide) {
          var escaped = JSON.stringify(editor.value);
          var packages = packagesUsedBy(editor.value);
          if (packages.length) consoleEl.textContent = "Loading " + packages.join(", ") + "…";
          return pyodide.loadPackage(packages).then(function () { return pyodide.runPythonAsync(
            "import io, sys, traceback\n" +
            "_portal_output = io.StringIO()\n" +
            "_portal_stdout = sys.stdout\n" +
            "sys.stdout = _portal_output\n" +
            "try:\n exec(" + escaped + ", {'__name__': '__main__'})\n" +
            "except Exception:\n traceback.print_exc(file=_portal_output)\n" +
            "finally:\n sys.stdout = _portal_stdout\n" +
            "_portal_output.getvalue()"
          ); });
        }).then(function (output) {
          lastOutput = String(output || "");
          consoleEl.textContent = lastOutput || "(No output)";
          return lastOutput;
        }).catch(function (error) {
          lastOutput = null;
          consoleEl.textContent = "Runner error: " + error.message;
          showResult(task, "❌ Your code could not run. Fix the error and try again.", false);
          return null;
        }).finally(function () { runButton.disabled = false; });
      }
      if (runButton) runButton.addEventListener("click", runCode);
      if (resetButton) resetButton.addEventListener("click", function () {
        editor.value = starter;
        lastOutput = null;
        consoleEl.textContent = "Run your code to see its output.";
        var result = task.querySelector(".code-result");
        if (result) { result.textContent = ""; result.className = "code-result"; }
      });
      if (checkButton) checkButton.addEventListener("click", function () {
        runCode().then(function (output) {
          if (output === null) return;
          var expected = practice ? practice.dataset.expected : "";
          var correct = !expected || normaliseOutput(output) === normaliseOutput(expected);
          if (correct) {
            showResult(task, "✅ Correct — next task unlocked.", true);
            markDone(task, true);
          } else {
            showResult(task, "❌ Incorrect — compare your output with the expected result, then retry or ask for a hint.", false);
          }
        });
      });
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

    updateTaskLocks();
    refresh();
  });
})();

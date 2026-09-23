/* Lesson document interactivity: progress bar, mark-done, and timed
 * solution reveals — saved to the server when the viewer is the lesson's
 * own student (data-can-edit="1"). In a database-free preview,
 * data-lesson-id is empty and nothing hits the network — the page still
 * works, it just doesn't persist. Practice code runs on the student's own
 * computer, never in the browser or on the server. */
(function () {
  "use strict";

  var HINT_SECONDS = 30;

  function getCookie(name) {
    var match = document.cookie.match("(^|;\\s*)" + name + "=([^;]*)");
    return match ? decodeURIComponent(match[2]) : null;
  }

  document.addEventListener("DOMContentLoaded", function () {
    var root = document.getElementById("lesson-root");
    var lessonId = root ? root.dataset.lessonId : "";
    var canEdit = !!(root && root.dataset.canEdit === "1" && lessonId);
    var pagePath = window.location.pathname.replace(/\/$/, "");
    var lessonBase = (root && root.dataset.lessonBase ? root.dataset.lessonBase : (lessonId ? pagePath : "")).replace(/\/$/, "");
    var csrftoken = getCookie("csrftoken");

    var practices = Array.prototype.slice.call(document.querySelectorAll(".practice[data-task-id]"));
    var fill = document.getElementById("lesson-fill");
    var count = document.getElementById("lesson-count");
    var doneMsg = document.getElementById("lesson-donemsg");
    var completeBtn = document.getElementById("lesson-complete-btn");
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

    function refreshCompletionButton(answered) {
      if (!completeBtn) return;
      var totalQuizzes = Number(completeBtn.dataset.quizTotal || 0);
      var answeredQuizzes = answered === undefined
        ? Number(completeBtn.dataset.quizAnswered || 0)
        : answered;
      completeBtn.disabled = answeredQuizzes < totalQuizzes;
      completeBtn.dataset.quizAnswered = String(answeredQuizzes);
    }

    refreshCompletionButton();

    function markDone(practice, done, save) {
      practice.classList.toggle("done", done);
      var dbtn = practice.querySelector(".dbtn");
      if (dbtn) dbtn.textContent = done ? "Done" : "Mark done";
      if (done && practice._cancelHintTimer) practice._cancelHintTimer();
      refresh();
      if (save !== false) {
        post(lessonBase + "/task/" + practice.dataset.taskId + "/complete/", { complete: done });
      }
    }

    // ---- hydrate saved state ----
    var stateEl = document.getElementById("lesson-state");
    var state = { completed: [], quiz_answers: {}, quiz_retry_at: {} };
    if (stateEl) {
      try { state = JSON.parse(stateEl.textContent); } catch (e) { /* ignore */ }
    }
    (state.completed || []).forEach(function (taskId) {
      var practice = document.querySelector('.practice[data-task-id="' + CSS.escape(taskId) + '"]');
      if (practice) markDone(practice, true, false);
    });

    // ---- mark-done ----
    practices.forEach(function (practice) {
      var dbtn = practice.querySelector(".dbtn");
      if (dbtn) {
        dbtn.addEventListener("click", function () {
          markDone(practice, !practice.classList.contains("done"));
        });
      }
    });

    // ---- solution reveal: nothing starts until the student clicks "I'm
    // stuck?" — that starts a countdown, which always has to finish on its
    // own before the solution shows. No way to skip ahead. ----
    practices.forEach(function (practice) {
      if (practice.dataset.hasSolution !== "1") return;

      var hbtn = practice.querySelector(".hbtn");
      var hint = practice.querySelector(".hint");
      var row = practice.querySelector(".practice-actions");
      var dbtn = practice.querySelector(".dbtn");
      if (!hbtn || !hint || !row) return;

      var started = false;
      var revealed = false;
      var timer = null;
      var iv = null;

      function reveal() {
        if (revealed) return;
        revealed = true;
        if (iv) clearInterval(iv);
        if (timer) { timer.remove(); timer = null; }
        hbtn.style.display = "none";
        hint.classList.add("show");
        hint.scrollIntoView({ behavior: "smooth", block: "nearest" });
        post(lessonBase + "/task/" + practice.dataset.taskId + "/reveal/", {});
      }

      practice._cancelHintTimer = function () {
        if (iv) clearInterval(iv);
        if (timer) { timer.remove(); timer = null; }
      };

      practice._startHintTimer = function () {
        if (started || revealed || practice.classList.contains("done")) return;
        started = true;
        hbtn.style.display = "none";

        timer = document.createElement("div");
        timer.className = "timer";
        var ring = document.createElement("div");
        ring.className = "ring";
        var label = document.createElement("span");
        timer.appendChild(ring);
        timer.appendChild(label);
        row.insertBefore(timer, dbtn);

        var left = HINT_SECONDS;
        var tick = function () {
          var m = Math.floor(left / 60), s = left % 60;
          label.textContent = "Answer in " + m + ":" + String(s).padStart(2, "0");
          ring.style.background = "conic-gradient(var(--amber) " + ((HINT_SECONDS - left) / HINT_SECONDS * 360) + "deg,var(--amberbg) 0deg)";
          if (left <= 0) {
            reveal();
            return;
          }
          left--;
        };
        tick();
        iv = setInterval(tick, 1000);
      };

      hbtn.addEventListener("click", function () {
        practice._startHintTimer();
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

    // ---- quiz options: graded and saved once per quiz when viewing your own
    // lesson; a plain preview (no lesson id) just shows feedback locally ----
    var scorePill = document.getElementById("lesson-quiz-score");

    function lockQuiz(quiz, selectedIndex, isCorrect) {
      quiz.querySelectorAll(".quiz-option").forEach(function (opt) {
        var picked = Number(opt.dataset.index) === selectedIndex;
        opt.classList.toggle("picked", picked);
        if (picked) opt.classList.toggle("correct", isCorrect);
        if (picked) opt.classList.toggle("incorrect", !isCorrect);
        opt.disabled = true;
        var wrap = opt.closest(".quiz-option-wrap");
        var feedback = wrap && wrap.querySelector(".quiz-feedback");
        if (picked && feedback) feedback.classList.add("show");
      });
    }

    function shuffleQuizOptions(quiz) {
      var container = quiz.querySelector(".quiz-options");
      var options = Array.prototype.slice.call(quiz.querySelectorAll(".quiz-option-wrap"));
      if (!container || options.length < 2) return;

      for (var index = options.length - 1; index > 0; index -= 1) {
        var swapIndex = Math.floor(Math.random() * (index + 1));
        var current = options[index];
        options[index] = options[swapIndex];
        options[swapIndex] = current;
      }
      options.forEach(function (option) { container.appendChild(option); });
    }

    document.querySelectorAll(".quiz[data-quiz-id]").forEach(shuffleQuizOptions);

    document.querySelectorAll(".quiz[data-quiz-id]").forEach(function (quiz) {
      var quizId = quiz.dataset.quizId;
      var saved = state.quiz_answers ? state.quiz_answers[quizId] : null;
      var retryAt = state.quiz_retry_at ? Date.parse(state.quiz_retry_at[quizId] || "") : NaN;
      if (saved && (!retryAt || retryAt > Date.now())) {
        lockQuiz(quiz, saved.selected_index, saved.is_correct);
        if (retryAt) {
          setTimeout(function () {
            quiz.querySelectorAll(".quiz-option").forEach(function (option) {
              option.disabled = false;
              option.classList.remove("picked", "correct", "incorrect");
              var feedback = option.closest(".quiz-option-wrap").querySelector(".quiz-feedback");
              if (feedback) feedback.classList.remove("show");
            });
          }, Math.max(0, retryAt - Date.now()));
        }
      }
    });

    document.querySelectorAll(".quiz-option").forEach(function (btn) {
      btn.addEventListener("click", function () {
        var quiz = btn.closest(".quiz[data-quiz-id]");
        if (!quiz || quiz.querySelector(".quiz-option[disabled]")) return;

        if (!canEdit) {
          btn.classList.add("picked");
          btn.classList.toggle("correct", btn.dataset.correct === "1");
          btn.classList.toggle("incorrect", btn.dataset.correct !== "1");
          var wrap = btn.closest(".quiz-option-wrap");
          var feedback = wrap && wrap.querySelector(".quiz-feedback");
          if (feedback) feedback.classList.add("show");
          return;
        }

        var quizId = quiz.dataset.quizId;
        var selectedIndex = Number(btn.dataset.index);
        post(lessonBase + "/quiz/" + encodeURIComponent(quizId) + "/answer/", { selected_index: selectedIndex })
          .then(function (res) { return res && res.json(); })
          .then(function (data) {
            if (!data || !data.ok) return;
            lockQuiz(quiz, data.selected_index, data.is_correct);
            refreshCompletionButton(Number(completeBtn && completeBtn.dataset.quizAnswered || 0) + 1);
            if (scorePill) scorePill.textContent = "Score: " + data.score_correct + " / " + data.score_total;
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

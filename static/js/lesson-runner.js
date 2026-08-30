/* In-browser Python execution for :::task runnable=python blocks, via
 * Pyodide (WebAssembly CPython) loaded from a CDN. Nothing runs on the
 * server — the code never leaves the student's browser. The Pyodide
 * runtime (a few MB) is only fetched if the page actually has a runner. */
(function () {
  "use strict";

  var PYODIDE_CDN = "https://cdn.jsdelivr.net/pyodide/v0.26.4/full/pyodide.js";
  var pyodideReadyPromise = null;

  function loadScript(src) {
    return new Promise(function (resolve, reject) {
      var s = document.createElement("script");
      s.src = src;
      s.onload = resolve;
      s.onerror = function () { reject(new Error("Could not load " + src)); };
      document.head.appendChild(s);
    });
  }

  function getPyodide() {
    if (!pyodideReadyPromise) {
      pyodideReadyPromise = loadScript(PYODIDE_CDN).then(function () {
        return window.loadPyodide();
      });
    }
    return pyodideReadyPromise;
  }

  function handleTab(textarea, e) {
    if (e.key !== "Tab") return;
    e.preventDefault();
    var start = textarea.selectionStart, end = textarea.selectionEnd;
    textarea.value = textarea.value.slice(0, start) + "    " + textarea.value.slice(end);
    textarea.selectionStart = textarea.selectionEnd = start + 4;
  }

  document.addEventListener("DOMContentLoaded", function () {
    var runners = document.querySelectorAll(".runner[data-runner]");
    if (!runners.length) return;

    runners.forEach(function (runner) {
      var editor = runner.querySelector(".runner-editor");
      var runBtn = runner.querySelector(".runner-run-btn");
      var status = runner.querySelector(".runner-status");
      var output = runner.querySelector(".runner-output");
      if (!editor || !runBtn) return;

      editor.addEventListener("keydown", function (e) { handleTab(editor, e); });

      runBtn.addEventListener("click", function () {
        if (runner.dataset.lang !== "python") return;
        runBtn.disabled = true;
        status.textContent = "Loading Python…";
        status.className = "runner-status";

        getPyodide().then(function (pyodide) {
          status.textContent = "Running…";
          var buffer = [];
          pyodide.setStdout({ batched: function (s) { buffer.push(s); } });
          pyodide.setStderr({ batched: function (s) { buffer.push(s); } });
          return pyodide.runPythonAsync(editor.value).then(function () {
            return buffer.join("\n");
          }, function (err) {
            buffer.push(String(err));
            return Promise.reject(buffer.join("\n"));
          });
        }).then(function (text) {
          output.hidden = false;
          output.className = "runner-output";
          output.textContent = text || "(ran with no output)";
          status.textContent = "Done";
        }).catch(function (errText) {
          output.hidden = false;
          output.className = "runner-output error";
          output.textContent = typeof errText === "string" ? errText : String(errText);
          status.textContent = "Error";
          status.className = "runner-status error";
        }).finally(function () {
          runBtn.disabled = false;
        });
      });
    });
  });
})();

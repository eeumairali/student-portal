/* Insert-snippet toolbar for the lesson Markdown textarea — so a tutor
 * doesn't need to already know the :::task syntax by heart. Inserts at the
 * cursor (or appends, with a blank line first, if nothing is focused). */
(function () {
  "use strict";

  var SNIPPETS = {
    code: [
      ":::task id=CHANGE_ID type=code hint=30",
      "Task title",
      "",
      "NOTE",
      "What the student should do (in Jupyter, Blender, MATLAB, etc.).",
      "",
      "EXPECTED",
      "expected output",
      "",
      "DONE WHEN",
      "what \"done\" looks like",
      "",
      "SOLUTION",
      "```python",
      "# solution code",
      "```",
      ":::",
    ].join("\n"),
    choice: [
      ":::task id=CHANGE_ID type=choice",
      "Question text",
      "",
      "OPTIONS",
      "- [x] correct option — why it's correct",
      "- wrong option — why it's wrong",
      ":::",
    ].join("\n"),
    step: [
      ":::task id=CHANGE_ID type=step hint=60",
      "Task title",
      "",
      "NOTE",
      "What to do in the other software.",
      "",
      "DONE WHEN",
      "what \"done\" looks like",
      ":::",
    ].join("\n"),
    blank: "{{blank_id}}",
  };

  function insertAtCursor(textarea, text) {
    var start = textarea.selectionStart;
    var end = textarea.selectionEnd;
    var before = textarea.value.slice(0, start);
    var after = textarea.value.slice(end);
    var needsLeadingBlank = before.length > 0 && !before.endsWith("\n\n") && !before.endsWith("\n");
    var insert = (needsLeadingBlank ? "\n\n" : "") + text + "\n";
    textarea.value = before + insert + after;
    var pos = (before + insert).length;
    textarea.focus();
    textarea.selectionStart = textarea.selectionEnd = pos;
  }

  document.addEventListener("DOMContentLoaded", function () {
    document.querySelectorAll("[data-editor-toolbar]").forEach(function (toolbar) {
      var targetId = toolbar.dataset.editorToolbar;
      var textarea = document.getElementById(targetId);
      if (!textarea) return;
      toolbar.querySelectorAll("[data-snippet]").forEach(function (btn) {
        btn.addEventListener("click", function () {
          var snippet = SNIPPETS[btn.dataset.snippet];
          if (snippet) insertAtCursor(textarea, snippet);
        });
      });
    });
  });
})();

/* Insert-snippet toolbar for the lesson Markdown textarea — so a tutor
 * doesn't need to already know the :::task syntax by heart. Inserts at the
 * cursor (or appends, with a blank line first, if nothing is focused). */
(function () {
  "use strict";

  function formatDateISO(date) {
    var year = date.getFullYear();
    var month = String(date.getMonth() + 1).padStart(2, '0');
    var day = String(date.getDate()).padStart(2, '0');
    return year + '-' + month + '-' + day;
  }

  var studentName = document.body.dataset.studentName || "student_username";
  var today = formatDateISO(new Date());

  var SNIPPETS = {
    student: [
      "---",
      "student: " + studentName,
      "date: " + today,
      "title: Placeholder title",
      "subtitle: Short description of the concept",
      "course: course-slug",
      "topics:",
      "  - Topic one",
      "  - Topic two",
      "hint_seconds: 240",
      "visible: false",
      "---",
      "",
    ].join("\n"),
    block: [
      "## Block title",
      "",
      "Short explanation of the idea in this block.",
      "",
      ":::example",
      "```python",
      "# a small worked example",
      "```",
      ":::",
      "",
      ":::practice id=CHANGE_ID hint=20",
      "What the student should try, on their own computer.",
      "",
      "EXPECTED",
      "expected output",
      "",
      "SOLUTION",
      "```python",
      "# solution code",
      "```",
      ":::",
    ].join("\n"),
    practice: [
      ":::practice id=CHANGE_ID hint=20",
      "What the student should try, on their own computer.",
      "",
      "EXPECTED",
      "expected output",
      "",
      "SOLUTION",
      "```python",
      "# solution code",
      "```",
      ":::",
    ].join("\n"),
    example: [
      ":::example",
      "```python",
      "# a small worked example",
      "```",
      ":::",
    ].join("\n"),
    tip: [
      ":::tip",
      "A short, useful note.",
      ":::",
    ].join("\n"),
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

  function bindToolbar() {
    document.querySelectorAll("[data-editor-toolbar]").forEach(function (toolbar) {
      var targetId = toolbar.dataset.editorToolbar;
      var textarea = document.getElementById(targetId);
      if (!textarea) return;
      toolbar.querySelectorAll("[data-snippet]").forEach(function (btn) {
        if (btn.__editorToolbarBound) return;
        btn.__editorToolbarBound = true;
        btn.addEventListener("click", function () {
          var snippet = SNIPPETS[btn.dataset.snippet];
          if (snippet) insertAtCursor(textarea, snippet);
        });
      });
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", bindToolbar, { once: true });
  } else {
    bindToolbar();
  }
})();

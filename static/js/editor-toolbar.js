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
    quiz: [
      ":::task id=CHANGE_ID type=choice",
      "Question text?",
      "",
      "OPTIONS",
      "- Wrong option — feedback for why it's wrong.",
      "- [x] Correct option — feedback for why it's right.",
      "- Another wrong option — feedback for why it's wrong.",
      ":::",
    ].join("\n"),
    task_step: [
      ":::task id=CHANGE_ID type=step hint=60",
      "Short instruction title",
      "",
      "NOTE",
      "What to do, step by step.",
      "",
      "DONE WHEN",
      "The observable sign it worked.",
      "",
      "SOLUTION",
      "If stuck, what to check.",
      ":::",
    ].join("\n"),
    task_code: [
      ":::task id=CHANGE_ID type=code hint=180",
      "Short task title",
      "",
      "NOTE",
      "Type this exactly, then run it.",
      "",
      "```python",
      "# code the student types",
      "```",
      "",
      "DONE WHEN",
      "The observable sign it worked.",
      "",
      "SOLUTION",
      "```python",
      "# what went wrong, or the full solution",
      "```",
      ":::",
    ].join("\n"),
    task_answer: [
      ":::task id=CHANGE_ID type=answer",
      "Short task title",
      "",
      "NOTE",
      "Try each of these, then fill in what happened: {{blank_name}}",
      "",
      "DONE WHEN",
      "All the blanks are filled in.",
      ":::",
    ].join("\n"),
    journey: [
      ":::journey",
      "- Stage one | Title | What they'll have made | done",
      "- Stage two — now | Title | What they'll have made | now",
      "- Stage three | Title | What they'll have made",
      ":::",
    ].join("\n"),
    figure: [
      ":::figure caption=\"Describe the diagram\"",
      "  draw ascii art or a small diagram here",
      ":::",
    ].join("\n"),
    objectives: [
      ":::objectives",
      "1. First goal.",
      "CHECK — the observable sign it worked.",
      "",
      "2. Second goal.",
      "CHECK — the observable sign it worked.",
      ":::",
    ].join("\n"),
    steps: [
      ":::steps",
      "1. First thing covered.",
      "2. Second thing covered.",
      "3. Third thing covered.",
      ":::",
    ].join("\n"),
    grid: [
      ":::grid",
      "Column one heading",
      "Item",
      "Item",
      "---",
      "Column two heading",
      "Item",
      "Item",
      ":::",
    ].join("\n"),
    push: [
      ":::push title=\"Call to action\"",
      "What the student should do before next time.",
      ":::",
    ].join("\n"),
    card: [
      ":::card title=\"Reference title\"",
      "Reference material or setup steps go here.",
      ":::",
    ].join("\n"),
    aside: [
      ":::aside title=\"Side-note title\"",
      "A definition or tangent worth flagging.",
      ":::",
    ].join("\n"),
    rule: [
      ":::rule title=\"Check the reasoning\"",
      "FIRST CASE",
      "Why it holds in this case.",
      "---",
      "SECOND CASE",
      "Why it holds in this case too.",
      ":::",
    ].join("\n"),
    checklist: [
      ":::checklist",
      "- First thing to check off",
      "- Second thing to check off",
      ":::",
    ].join("\n"),
  };

  var ARTICLE_SNIPPETS = {
    text: "Write a paragraph explaining the idea in your own words.",
    heading: "## Section heading",
    code: [
      "```python",
      "# Add your example here",
      "print(\"hello world\")",
      "```",
    ].join("\n"),
    table: [
      "| Item | Description |",
      "| --- | --- |",
      "| Example | Add a row here |",
      "| Another item | Add more details |",
    ].join("\n"),
    image: "![Describe the image](https://example.com/image.jpg)",
    list: [
      "- First point",
      "- Second point",
      "- Third point",
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
          var snippets = toolbar.dataset.editorKind === "article" ? ARTICLE_SNIPPETS : SNIPPETS;
          var snippet = snippets[btn.dataset.snippet];
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

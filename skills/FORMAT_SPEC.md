# Lesson format specification

One authoring format for every lesson: **Markdown with YAML front matter**.
Deliberately small on purpose — a tutor writes it, or an AI adapts existing
slides/notebook content into it. There is exactly one visual style, always
colorful: numbered blocks, a distinct example panel, and self-practice
questions the student works out on their own computer (Blender, Jupyter,
Arduino IDE, MATLAB — wherever the real work happens), never in the browser.

`LESSON_TEMPLATE.md` is a worked example of every construct below.

---

## 1. Front matter

```yaml
---
student: andy                  # required — username of the student
date: 2026-08-31               # required — YYYY-MM-DD, orders the timeline
title: Recursion, one branch at a time   # required
subtitle: The idea the whole week rests on   # optional
course: blender-python          # optional — groups lessons; created if missing
topics:                          # optional — shown as pills under the title
  - Base case vs recursive case
  - Stack depth
hint_seconds: 20                 # optional — default reveal timer, default 20
visible: false                   # optional — default false; tutor publishes
week: 5                          # unknown key — becomes a header pill
platform: preply                 # unknown key — becomes a header pill
---
```

### Known vs unknown keys

**Known keys**: `student`, `date`, `title`, `subtitle`, `course`, `topics`,
`hint_seconds`, `visible`, `accent`. These drive behaviour and map to model
fields.

**Unknown keys** are not an error. Store them verbatim in a `JSONField`
called `meta` and render each as a header pill, in file order. Adding
`week: 5` next month requires no code change.

### Validation

- Missing `student`, `date` or `title` → reject the upload, show which is missing.
- `student` that doesn't exist → reject, offer the list of students. Never create
  a student implicitly.
- `date` that isn't ISO → reject with the expected shape.
- Duplicate `student` + `date` + `title` → offer to update the existing lesson
  rather than creating a second one.

---

## 2. Blocks

The body is a sequence of numbered blocks. Each `## ` heading starts a new
block; the renderer counts them and labels each "N of TOTAL" automatically —
number them however you like in the source, the count always matches.

```markdown
## Base case and recursive case

A recursive function needs a base case (when to stop) and a recursive case
(the call that gets closer to the base case).

:::example
```python
def countdown(n):
    if n == 0:
        print("done")
        return
    print(n)
    countdown(n - 1)
```
:::

:::tip
If a recursive function is missing a base case, it recurses forever —
Python stops it with a RecursionError.
:::

:::practice id=p1 hint=20
Write `factorial(n)` that returns n!, using recursion. Run it in your own
Python environment.

EXPECTED
factorial(5) -> 120

SOLUTION
```python
def factorial(n):
    return 1 if n == 0 else n * factorial(n - 1)
```
:::

## Stack depth

...next block...
```

Anything before the first `## ` heading (an intro paragraph, an objectives
list) renders as an unnumbered block above "1 of TOTAL".

### Ordinary Markdown

Standard Markdown works everywhere inside and between blocks: paragraphs,
bold, italic, links, lists, tables, fenced code blocks, blockquotes. Only
`## ` is special — it is reserved for block boundaries. Use `###` (or plain
text) for anything inside a block that doesn't need its own numbered step.

---

## 3. The three block-level constructs

All use `:::name` … `:::` fencing.

| construct | purpose |
|---|---|
| `:::example` | a colored panel holding a worked example — code, a diagram, a short explanation |
| `:::tip` | a short amber note — a warning, a reminder, an aside |
| `:::practice id=… hint=N` | a self-practice question, timer-gated solution |

### `:::practice`

```
:::practice id=p1 hint=20
Question text. What exactly should the student write and run — on their own
computer, never on this site.

EXPECTED
what the correct output looks like

SOLUTION
```python
# the answer, revealed only after the hint timer (or instantly with hint=0)
```
:::
```

- `id` — **required.** Stable identifier; a student's "done" state and hint
  reveals are keyed on it. Changing it loses that history.
- `hint` — seconds before the SOLUTION unlocks after the student clicks
  "I'm stuck". Falls back to `hint_seconds` from the front matter (default
  20). `hint=0` reveals instantly.
- `EXPECTED` is optional — the student compares their own output against it.
- `SOLUTION` is optional. A practice question with no `SOLUTION` shows no
  hint button at all — legitimate for "try it and see what happens" tasks
  where revealing the answer would remove the point of the exercise.
- Marking a practice "done" is always the student's own click — there is no
  automatic checking, because the code never runs on this site.

---

## 4. Attached files

A lesson can carry files (slides, a notebook, a dataset) via the tutor
upload page, same as before — these are downloads, not embedded in the
markdown. Link to a lesson's files from the block text if useful ("see the
attached slides for the diagram"); the download button itself is shown
automatically wherever the lesson has files attached.

---

## 5. Parsing and storage

**Parse on save, store both.** Keep the raw markdown in a `TextField` — it is
the source of truth and what the tutor edits. Derive `Task` rows (one per
`:::practice`) from it on every save.

**Reconciliation rule.** On re-parse, match practice questions by `id`:

- id present in both → update content, keep progress
- id in file but not database → create
- id in database but not file → mark orphaned, **never delete**, and warn the
  tutor in the preview: "2 practice questions removed — the student has
  progress on them."

**Preview before commit.** Every paste and upload shows: student, date,
block count, practice-question count, any warnings, and the rendered body.
Nothing saves until the tutor confirms.

---

## 6. What the tutor sees

For each student, per lesson: which practice questions were completed, and
**which solutions were revealed and when**. The reveal log is the most
useful signal — it shows where the student actually struggled, which a
completion tick does not.

---

## 7. Adapting existing content with AI

Give an AI your existing slides, notebook, or notes plus this file and
`LESSON_TEMPLATE.md`, and ask it to restructure the content into this format:
front matter with `student`, `date`, `title`, and `topics`; one `## ` block
per concept; a `:::example` per block where a worked example exists; one or
more `:::practice` questions per block with a real `EXPECTED` result. Keep
the student's original wording where it's already clear — the point of the
format is structure and pacing, not rewriting content that already works.

# Lesson format specification

One authoring format for every lesson: **Markdown with YAML front matter**.
A tutor writes it, or an AI adapts existing slides/notebook content into it.
There is exactly one visual style, always colorful: numbered blocks, and a
fixed set of block-level constructs below.

**This file is the single source of truth for what this app can render.**
If a block type isn't listed in section 3, the parser does not know it —
it falls through to a plain-text warning and loses all structure/styling.
**Do not invent new `:::name` block types.** If existing content uses one
that isn't listed here, either rewrite it into an existing block, or ask
for the block type to be added to the parser (`learning/lesson_markdown.py`)
and this spec *before* writing lesson content that assumes it exists.

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
`week: 5` next month requires no code change. This is also how a `:::task`
question knows it's a "project" marker vs a plain lesson — see the tutor
notes in `learning/views.py` for the `project` meta key convention.

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

Anything before the first `## ` heading (an intro paragraph, a journey map)
renders as an unnumbered block above "1 of TOTAL".

### Ordinary Markdown

Standard Markdown works everywhere inside and between blocks: paragraphs,
bold, italic, links, lists, tables, fenced code blocks, blockquotes. Only
`## ` is special — it is reserved for block boundaries. Use `###` (or plain
text) for anything inside a block that doesn't need its own numbered step.

---

## 3. Block-level constructs

All use `:::name` … `:::` fencing, with optional `key=value` (or
`key="value with spaces"`) attributes on the opening line.

| construct | purpose |
|---|---|
| `:::example` | a colored panel holding a worked example — code, a diagram, a short explanation |
| `:::tip` | a short amber note — a warning, a reminder, an aside |
| `:::practice id=… hint=N` | a self-practice question, timer-gated solution, tracked per student |
| `:::task id=… type=choice` | an ungraded multiple-choice warm-up question, per-option feedback |
| `:::journey` | a horizontal roadmap of stages (a course/week overview) |
| `:::figure caption="…"` | preformatted ASCII art or a small diagram, with a caption |
| `:::objectives` | a numbered list of goals, each with an optional success check |
| `:::grid` | two (or more) side-by-side comparison columns |
| `:::push title="…"` | a callout / call-to-action banner |
| `:::checklist` | a client-side, self-tick checklist (not saved to the server) |

### `:::example`

```
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
```

Any markdown content — usually a fenced code block, sometimes prose or a
small diagram.

### `:::tip`

```
:::tip
If a recursive function is missing a base case, it recurses forever —
Python stops it with a RecursionError.
:::
```

Plain markdown, rendered in an amber note panel.

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
  reveals are keyed on it and saved server-side. Changing it loses that history.
- `hint` — seconds before the SOLUTION unlocks after the student clicks
  "I'm stuck". Falls back to `hint_seconds` from the front matter (default
  20). `hint=0` reveals instantly.
- `EXPECTED` is optional — the student compares their own output against it.
- `SOLUTION` is optional. A practice question with no `SOLUTION` shows no
  hint button at all — legitimate for "try it and see what happens" tasks
  where revealing the answer would remove the point of the exercise.
- Marking a practice "done" is always the student's own click — there is no
  automatic checking, because the code never runs on this site.
- The code the student writes always runs on their own computer — this app
  never executes code in the browser or on the server.

### `:::task id=… type=choice` — ungraded multiple-choice

```
:::task id=q1 type=choice
Which one stores your name?

OPTIONS
- [x] `name = "Harel"` — Yes! Quotes = text.
- `name = Harel` — No quotes, so Python gets confused.
- `name == "Harel"` — Two `=` asks a question instead.
:::
```

- `id` — required; a temporary one is auto-assigned (with a warning) if
  missing. Used only to keep option ordering stable — **not** saved
  server-side; nothing about a student's answer choice is persisted.
- `type=choice` is required — it's the only supported task type right now.
- The question is everything before the literal `OPTIONS` line (markdown).
- Each option is one `- ` list line. Mark the correct one with a leading
  `[x]` (or `[X]`); leave the others plain.
- Split the option's own label from its feedback with an em dash ` — `
  (or ` -- ` / ` - ` as a fallback). Every option — right or wrong — should
  carry its own short feedback message; clicking an option reveals it.
- This is a warm-up/engagement tool, not a graded quiz — a student can click
  more than one option, and nothing is scored or saved.

### `:::journey` — roadmap of stages

```
:::journey
- Weeks 1–3 🐍 | Python | Mini-games you play | now
- Weeks 4–5 🎨 | Turtle + Games | Your own game
- Weeks 6–8 💡 | Circuits | Traffic light that runs itself
- Weeks 9–12 🤖 | Robots | A robot that follows a line
:::
```

One `- ` line per stage, four `|`-separated fields: **time/label**,
**title**, **detail**, and an optional 4th field — the literal word `now`
marks that stage as the current one (highlighted). The last field is
optional; omit it if no stage should be highlighted.

### `:::figure caption="…"` — ASCII art / small diagram

```
:::figure caption="Where we're going 🚀"
   🐍  ──▶  🎨  ──▶  💡  ──▶  🤖
 code    games   circuits   ROBOT!
:::
```

The content is shown verbatim in a monospace block (whitespace and
alignment preserved) — don't run it through markdown formatting. `caption`
is optional, shown centered below the art.

### `:::objectives` — numbered goals with success checks

```
:::objectives
1. 🐍 Make the computer do what you say.
CHECK — your family can't beat your guessing game.

2. 🤖 Make a robot decide for itself.
CHECK — it follows a black line, nobody touching it.
:::
```

A numbered (`1.`, `2.`, …) list; the number itself doesn't matter, items
are read in order. A `CHECK` line right after an item (any dash style after
the word `CHECK`) is optional — it's the observable "you'll know it worked
when…" success criterion, shown as a smaller line under the goal.

### `:::grid` — side-by-side comparison columns

```
:::grid
✅ YOU NEED
💻 Laptop
🎧 Headphones
🌐 Chrome
---
🚫 YOU DON'T NEED
❌ Any install
❌ Any money
:::
```

Plain lines (no `- ` prefix), split into columns by a line that is exactly
`---`. Each column's first line is its heading; the rest are its items.
Works with two columns or more.

### `:::push title="…"` — callout / call to action

```
:::push title="Bring one idea on Tuesday 🎯"
Think of a game, app or robot you love.

**What does it do that made you think "how did they DO that?"**
:::
```

`title` is optional; the body is ordinary markdown, shown in an accented
callout panel.

### `:::checklist`

```
:::checklist
- Zoom tested
- Cheat sheet printed
- Warm-up questions answered
:::
```

A `- ` list. Purely a client-side memory aid the student can tick off in
the browser — **not saved anywhere**, resets on reload. Unlike
`:::practice`, there's no `id` and no server-side tracking; use `:::practice`
instead of `:::checklist` for anything that needs to persist.

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
`:::practice`) from it on every save. `:::task` (multiple-choice) and
`:::checklist` are **not** persisted — they're purely rendered client-side
from the markdown on every view, nothing to reconcile.

**Reconciliation rule.** On re-parse, match `:::practice` questions by `id`:

- id present in both → update content, keep progress
- id in file but not database → create
- id in database but not file → mark orphaned, **never delete**, and warn the
  tutor in the preview: "2 practice questions removed — the student has
  progress on them."

**Preview before commit.** Every paste and upload shows: student, date,
block count, practice-question count, any warnings (including "Unknown
block type" for anything not in section 3), and the rendered body. Nothing
saves until the tutor confirms.

---

## 6. What the tutor sees

For each student, per lesson: which practice questions were completed, and
**which solutions were revealed and when**. The reveal log is the most
useful signal — it shows where the student actually struggled, which a
completion tick does not. Multiple-choice (`:::task`) answers and checklist
ticks are not tracked — they're ungraded warm-up/self-check tools by design.

---

## 7. Adapting existing content with AI

Give an AI your existing slides, notebook, or notes **plus this file** and
`LESSON_TEMPLATE.md`, and ask it to restructure the content into this
format: front matter with `student`, `date`, `title`, and `topics`; one
`## ` block per concept; the right construct from section 3 for each piece
of content (an `:::example` for a worked example, `:::journey` for a
roadmap overview, `:::task type=choice` for a warm-up question, and so on).
Keep the student's original wording where it's already clear — the point of
the format is structure and pacing, not rewriting content that already
works.

**Before generating any lesson markdown, re-read section 3 above and use
only the block types listed there.** If the source content needs something
that doesn't map to an existing block (a video embed, a poll, whatever),
say so explicitly instead of inventing a new `:::name` — flag it as
"unsupported: needs a new block type" so a human can decide whether to add
real parser/template support for it.

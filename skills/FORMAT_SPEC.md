# Lesson format specification

One authoring format for every lesson: **Markdown with YAML front matter**.
Any subject, any student, any age group. The format changes how it looks; the file
never changes shape.

This document is the contract between what the tutor writes and what the parser
produces. `LESSON_TEMPLATE.md` is a working example of every construct below.

---

## 1. Front matter

```yaml
---
# before making anything confirm from user 
student: andy                  # required — username of the student
date: 2026-08-26               # required — YYYY-MM-DD, orders the timeline
title: One branch, and a function that calls itself   # required ask from user
subtitle: Recursion — the idea the whole week rests on
course: blender-python         # optional — groups lessons; created if missing
format: slide                  # optional — document | slide, default document
hint_seconds: 30              # optional — default timer, default 30
visible: false                 # optional — default false; tutor publishes
duration: 50 min
platform: preply               # unknown key — becomes a header pill
---
```

### Known vs unknown keys

**Known keys** (the list above minus `week` and `platform`) drive behaviour and
map to model fields.

**Unknown keys** are not an error. Store them verbatim in a `JSONField` called
`meta` and render each as a header pill, in file order. This is the whole
extensibility story — adding `topic: recursion` next month requires no code
change, and `meta` is queryable for later filtering.

Reserved key names that must NOT become pills: everything in the known list.

### Validation

- Missing `student`, `date` or `title` → reject the upload, show which is missing.
- `student` that doesn't exist → reject, offer the list of students. Never create
  a student implicitly.
- `date` that isn't ISO → reject with the expected shape.
- Duplicate `student` + `date` + `title` → offer to update the existing lesson
  rather than creating a second one.

---

## 2. Body

Standard Markdown works everywhere: headings, paragraphs, bold, italic, links,
lists, tables, fenced code blocks, blockquotes.

Two additions: **blanks** (inline) and **blocks** (fenced).

---

## 3. Blanks

Saved, per-student answer fields. They can appear in any prose, list item, or
table cell.

| syntax | renders as |
|---|---|
| `{{t1_z}}` | short inline input, ~110px |
| `{{t4_pattern\|wide}}` | full-width single-line input |
| `{{t5_why\|long}}` | multi-line textarea |

The id (`t1_z`) must be unique within the lesson. Ids are how answers are stored,
so **changing an id orphans that answer** — treat them like task ids.

In a Markdown table, a blank in a cell makes a fill-in table. No extra syntax:

```markdown
| depth | branches |
|---|---|
| 1 | {{t4_d1}} |
| 2 | {{t4_d2}} |
```

Blanks save on blur and on a debounce while typing. They do not gate completion —
a task is complete when the student says so, or when a choice is answered
correctly.

---

## 4. Tasks

```
:::task id=t1 type=code hint=240
One branch, by hand

NOTE
Write a script that clears the scene and draws one vertical branch.

Work out its middle point first — z = {{t1_z}}

```python
# YOUR CODE HERE
```

EXPECTED
(1002, 9)

DONE WHEN
A thin post stands on the floor, not half-buried and not floating.

SOLUTION
```python
bpy.ops.mesh.primitive_cylinder_add(radius=0.2, depth=2, location=(0, 0, 1))
```
A branch 2 long starting at z = 0 ends at z = 2, so its middle is at z = 1.
:::
```

### Attributes

| attribute | meaning |
|---|---|
| `id` | **required.** Stable identifier. Progress rows point at it. |
| `type` | `code` · `choice` · `step` · `answer`. Default `code`. |
| `hint` | Seconds before SOLUTION unlocks. Falls back to `hint_seconds`. `hint=0` means reveal instantly. |

### Sections inside a task

Recognised by a bare keyword on its own line. All optional except the first line,
which is always the task title.

- `NOTE` — supporting instruction under the title
- `EXPECTED` — the green expected-output box
- `DONE WHEN` — the green self-check criterion
- `SOLUTION` — revealed after the timer
- `OPTIONS` — only for `type=choice`

Everything between the title and the first keyword is body content: prose, code
fences, tables, blanks, nested blocks.

### Task types

**`code`** — writes code elsewhere (Blender, Jupyter, MATLAB) and self-marks.
Optionally has EXPECTED to compare against.

Interactive code tasks provide an editable Python editor, Run code, output
console, Reset, and Submit / check. The learner's code runs locally in the
browser and its normalised output is checked against `EXPECTED`. Add an
optional `STARTER` section for a small scaffold only, never a full solution.

For a timed self-practice task, use `phase=self` (or an `sp...` id such as
`sp1`) with `hint=60`. The one-minute countdown begins when the task unlocks
after the preceding task passes.

**`choice`** — multiple choice, instant feedback, marks itself complete on a
correct answer. No timer.

```
:::task id=q1 type=choice
Which one gives you the number of rows and columns?

OPTIONS
- [x] df.shape — shape is an attribute, a fact the table already knows, so no brackets.
- df.shape() — not this one. Is it DOING a job, or IS it a fact?
:::
```

`- [x]` marks the correct option. Text after `—` on each line is the feedback
shown when that option is picked. If a wrong option has no feedback, use a
generic line.

**`step`** — follow an instruction in other software (Tinkercad, Webots, Blender
UI). No output to check. Ticks done.

**`answer`** — a written answer in a `|long` blank, self-marked after the
solution unlocks.

### No SOLUTION is legitimate

Tasks whose whole point is observation ("run it at five depths and find the
pattern") must not offer a hint button — revealing the answer removes the task.
If a task has no `SOLUTION` section, render no hint button and no timer.

---

## 5. Blocks

All use `:::name` … `:::` fencing. Attributes as `key=value`, quoted if spaced.

| block | purpose | notes |
|---|---|---|
| `:::tip` | the amber `!` bar | one short paragraph |
| `:::card title="…"` | white panel | for "Before you start", reference tables |
| `:::rule title="…"` | dark teal panel | columns separated by a line containing only `---` |
| `:::steps` | big numbered items | one per list item |
| `:::grid` | equal columns | separated by `---`; first line of each is its label |
| `:::figure caption="…"` | monospace diagram | contents rendered verbatim |
| `:::objectives` | objective list | see below |
| `:::journey` | the day/session strip | see below |
| `:::aside title="…"` | untimed collapsible | for optional depth, never for answers |
| `:::push title="…"` | the closing question | dark panel, usually holds a `|long` blank |
| `:::checklist` | end-of-lesson ticks | list items become saved checkboxes |
| `:::raw` | escape hatch | contents inserted as HTML, sanitised |

Blocks may nest one level: a `:::tip` inside a `:::task` is valid and used often.

### `:::objectives`

```
:::objectives
1. Place a cylinder anywhere, at any angle, using only code.
WHY — a branch is a cylinder at an angle. Everything else is repetition.
CHECK — you make a branch leaning 30° and it lands where you predicted.
:::
```

### `:::journey`

```
:::journey
- Day 1 — today | One branch, then recursion | A Y that becomes a 4-way split | now
- Day 2 — Thursday | Randomness and parameters | A whole tree, different every run
- Day 3 — Friday | Keyframes | The tree grows, or sways | done
:::
```

Pipe-separated: label, focus, outcome, and an optional state of `now` or `done`.

### `:::checklist`

Each item becomes a checkbox saved against the student, id derived from position
(`check_1`, `check_2`). Because these ids are positional, reordering the checklist
shifts them — acceptable, since checklist state is low-value compared to answers.

### `:::raw`

The escape hatch. Sanitise with a strict allowlist: no `<script>`, no `on*`
attributes, no `<iframe>` except from a configured host allowlist. This exists so
the vocabulary doesn't have to grow for one-off needs — track how often it's used,
because a recurring `raw` pattern is a missing block.

---

## 6. Formats

Exactly two, set per lesson via `format:`. **Same templates, same tokens —
format is a CSS skin, not a fork.** Do not build a third.

### Shared structure

Every format renders: header (eyebrow, title, subtitle, pills), sticky progress
bar, body blocks, tasks, finish panel. The markdown never changes shape between
formats — only how it's styled.

### `document` — the default

Long-form, scrolling, dense enough to hold a full session: reference tables,
code, tasks with timers, all visible at once. This is the approved house style,
matching the original Ward Round HTML. When in doubt, this is what everything
should look like.

### `slide`

Same content, same constructs — restyled for a punchier, presentation-like
read. Bigger type, more whitespace, and each major section (a `##` heading, a
task, a block) reads as its own distinct beat in the scroll rather than
blending into a dense page. Still one continuous page — no click-through
slideshow, no JavaScript navigation, just a bolder rhythm.

### Implementation

CSS custom properties on `<body class="format-document">` / `class="format-slide"`.
One stylesheet, tokens shared between the two, plus a slide-specific block of
overrides for spacing and type scale. Per-lesson `accent: "#F4845F"` overrides
the primary action colour only. Nothing in front matter may inject arbitrary CSS.

---

## 7. Parsing and storage

**Parse on save, store both.** Keep the raw markdown in a `TextField` — it is the
source of truth and what the tutor edits. Derive `Task` rows from it on every save.

**Reconciliation rule.** On re-parse, match tasks by `id`:

- id present in both → update content, keep progress
- id in file but not database → create
- id in database but not file → mark orphaned, **never delete**, and warn the
  tutor in the preview: "3 tasks removed — 2 students have answers on them."

Never key progress on position. Blanks follow the same rule, keyed on blank id.

**Preview before commit.** Every paste and upload shows: student, date, format,
task count, blank count, any warnings, and the rendered body. Nothing saves until
the tutor confirms. Prefilling the form from a filename (`Andy_W3D2_Topic.pptx`
→ student Andy, week 3, day D2) is fine; silent filing is not.

---

## 8. What the tutor sees

For each student, per lesson: every blank's saved text, every checkbox, which
tasks were completed, and **which solutions were revealed**. The reveal log is the
most useful signal in the system — it shows where the student actually struggled,
which the completion percentage does not.

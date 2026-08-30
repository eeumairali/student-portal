# Lesson format specification

One authoring format for every lesson: **Markdown with YAML front matter**.
Any subject, any student, any age group. The theme changes how it looks; the file
never changes shape.

This document is the contract between what the tutor writes and what the parser
produces. `LESSON_TEMPLATE.md` is a working example of every construct below.

---

## 1. Front matter

```yaml
---
student: andy                  # required — username of the student
date: 2026-08-26               # required — YYYY-MM-DD, orders the timeline
title: One branch, and a function that calls itself   # required
subtitle: Recursion — the idea the whole week rests on
course: blender-python         # optional — groups lessons; created if missing
theme: professional            # optional — kids | beginner | professional
hint_seconds: 240              # optional — default timer, default 30
visible: false                 # optional — default false; tutor publishes
time: "7:00 PM"
duration: 45 min
week: 3                        # unknown key — becomes a header pill
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
| `runnable` | `type=code` only. Currently just `python`. Adds a live in-browser editor and Run button — see below. |

### Sections inside a task

Recognised by a bare keyword on its own line. All optional except the first line,
which is always the task title.

- `NOTE` — supporting instruction under the title
- `EXPECTED` — the green expected-output box
- `DONE WHEN` — the green self-check criterion
- `SOLUTION` — revealed after the timer
- `OPTIONS` — only for `type=choice`
- `STARTER` — only for `runnable=python`; the code the editor opens with

Everything between the title and the first keyword is body content: prose, code
fences, tables, blanks, nested blocks.

### Task types

**`code`** — writes code elsewhere (Blender, Jupyter, MATLAB) and self-marks.
Optionally has EXPECTED to compare against. For plain Python, add
`runnable=python` instead of sending the student to a separate notebook —
this renders a real code editor and a Run button on the page itself,
executing entirely in the browser (nothing is sent to a server):

```
:::task id=r1 type=code runnable=python hint=30
Double it

STARTER
```python
def double(x):
    return x

print(double(3))
```

EXPECTED
6

DONE WHEN
print(double(3)) shows 6

SOLUTION
```python
def double(x):
    return x * 2
```
:::
```

`STARTER` is literal code, not prose — fence it or leave it bare, either
works. Only Python is supported; `runnable` on anything else is ignored with
a warning, since Blender/MATLAB/Arduino code can't run in a browser tab.

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

## 6. Themes

Three, set on the student and overridable per lesson. **Same templates, different
tokens plus a few flags.** Do not fork the template tree.

### Shared structure

Every theme renders: header (eyebrow, title, subtitle, pills), sticky progress
bar, body blocks, tasks, finish panel. Only tokens and flags differ.

### `beginner` — the default

This is the approved house style, matching the existing Ward Round HTML. When in
doubt, this is what everything should look like.

```
--ink:#0C2429  --deep:#04434A  --teal:#028090  --sea:#00A896  --mint:#02C39A
--paper:#F2F8F8  --card:#FFFFFF  --line:#D6E6E7  --muted:#5C7A82
--amber:#B36B00  --amberbg:#FFF4E0  --green:#0A7A45  --greenbg:#E3F6EC
--code:#0F3239  --codetext:#9FE8DC  --violet:#5B3E96  --violetbg:#F1ECFB
display: Georgia, serif
body: "Segoe UI", system-ui, sans-serif        base 16px / 1.6
mono: "SFMono-Regular", Consolas, monospace
radius: 12px    density: normal
flags: tasks_all_visible, celebrate_on_complete
```

### `kids`

Warmer, larger, one task at a time so the page is never intimidating. Emoji
allowed in headings. Same information, less of it on screen at once.

```
--ink:#20303A  --deep:#1B6B63  --teal:#12897E  --sea:#00A896  --mint:#3FD9B8
--paper:#FFF9F0  --card:#FFFFFF  --line:#F0E2CE  --muted:#6E7F86
--coral:#F4845F  --coralbg:#FFEDE5  --sun:#FFC857  --sunbg:#FFF6DE
--amber:#C2681B  --amberbg:#FFF1DC  --green:#12894F  --greenbg:#E1F7EA
--code:#123A38  --codetext:#A8F0DE
display: "Fredoka", "Baloo 2", Georgia, sans-serif
body: "Nunito", "Segoe UI", sans-serif          base 17.5px / 1.7
mono: "JetBrains Mono", Consolas, monospace
radius: 18px    density: roomy
accent for primary actions: --coral
flags: tasks_one_at_a_time, celebrate_on_complete, big_task_numbers, show_emoji
```

`tasks_one_at_a_time`: within a section, show the current task; completed ones
collapse to a single tick line; later ones are dimmed until reached. Never hide
the reference material — only tasks.

### `professional`

Denser, quieter, everything on screen. No celebration animation. For university
and adult learners.

```
--ink:#0F1F24  --deep:#0B3B42  --teal:#0B6B78  --sea:#12808C  --mint:#1FA894
--paper:#F7FAFA  --card:#FFFFFF  --line:#DDE7E9  --muted:#5A7178
--amber:#8A5A12  --amberbg:#FBF3E4  --green:#12633F  --greenbg:#EAF4EE
--code:#0C2A30  --codetext:#8FD9CC  --violet:#4A3580  --violetbg:#EFEBF8
display: "IBM Plex Serif", Georgia, serif
body: "IBM Plex Sans", system-ui, sans-serif    base 15px / 1.55
mono: "IBM Plex Mono", Consolas, monospace
radius: 8px     density: compact
flags: tasks_all_visible, no_celebration, compact_header
```

### Implementation

CSS custom properties on `<body class="theme-kids">`. One stylesheet, three
`:root`-scoped variable sets, plus a handful of flag-driven rules. A fourth theme
should be a ~40 line addition, not a new template directory.

Per-lesson `accent: "#F4845F"` overrides the primary action colour only. Nothing
in front matter may inject arbitrary CSS.

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

**Preview before commit.** Every paste and upload shows: student, date, theme,
task count, blank count, any warnings, and the rendered body. Nothing saves until
the tutor confirms. Prefilling the form from a filename (`Andy_W3D2_Topic.pptx`
→ student Andy, week 3, day D2) is fine; silent filing is not.

---

## 8. What the tutor sees

For each student, per lesson: every blank's saved text, every checkbox, which
tasks were completed, and **which solutions were revealed**. The reveal log is the
most useful signal in the system — it shows where the student actually struggled,
which the completion percentage does not.

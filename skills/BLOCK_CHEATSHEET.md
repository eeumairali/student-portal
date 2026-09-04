# Lesson block cheat-sheet

Quick-reference for every `:::name` block the renderer supports. This is a
condensed companion to `FORMAT_SPEC.md` (the full spec — read that for
exact parsing rules, edge cases, and persistence behaviour) and
`LESSON_TEMPLATE.md` (a full worked lesson using every block below).

**Don't invent a `:::name` not on this list** — it renders as plain text
with a warning. If you need something new, add real parser/template
support first (`learning/lesson_markdown.py`) and document it in
`FORMAT_SPEC.md` and here.

The body is a sequence of `## ` headings (auto-numbered blocks); each can
hold any mix of the constructs below plus ordinary Markdown.

---

## Content panels

### `:::example`
A colored panel for a worked example — usually a fenced code block.
```
:::example
```python
def countdown(n):
    if n == 0:
        return
    print(n)
    countdown(n - 1)
```
:::
```

### `:::tip`
A short amber note — a warning, reminder, or aside.
```
:::tip
`z` is UP in Blender, not `y`.
:::
```

### `:::card title="…"`
A quiet, neutral panel for reference material or setup steps. `title` optional.
```
:::card title="Reference — every line you need tonight"
| line | what it does |
|---|---|
| `import bpy` | opens the door between Python and Blender |
:::
```

### `:::aside title="…"`
A titled side-note — a definition or tangent, dashed border. `title` optional.
```
:::aside title="What a function actually is"
Writing the job and doing the job are two separate things.
:::
```

### `:::push title="…"`
An accented callout / call-to-action banner. `title` optional.
```
:::push title="Bring one idea on Tuesday"
Think of a game, app or robot you love.
:::
```

### `:::rule title="…"`
A titled list of worked checks, split into groups by a lone `---` line.
Each group's first line is its heading. `title` optional.
```
:::rule title="Check the maths before you trust it"
IF THE TILT IS 0 — STRAIGHT UP
`sin(0) = 0`, so it doesn't move sideways. Correct.
---
AND THE HEIGHT
`cos(0) = 1`, so it moves the full length upward. Correct.
:::
```

---

## Tracked tasks (saved server-side, per student)

### `:::practice id=… hint=N`
A self-practice question — code runs on the student's own computer, never
here. Timer-gated `SOLUTION` reveal (`hint=` seconds, default from front
matter's `hint_seconds`). `EXPECTED` and `SOLUTION` both optional.
```
:::practice id=p1 hint=20
What should the student write and run?

EXPECTED
what the correct output looks like

SOLUTION
```python
# the answer
```
:::
```

### `:::task id=… type=step|code|answer hint=N`
A generalised tracked task step — shares progress/hint mechanics with
`:::practice`. First line (before any keyword) is the title.
- `NOTE` — optional instructions, often a fenced code block.
- `DONE WHEN` — optional observable success criterion.
- `SOLUTION` — optional, same timer-gated reveal as `:::practice`.
- A `:::tip` may be nested inside `NOTE`/`DONE WHEN`/`SOLUTION` — nothing else may nest.

`type=step` — a plain instruction, no code expected:
```
:::task id=s1 type=step hint=60
Find the Scripting tab

NOTE
Click the Scripting tab, then click New.

DONE WHEN
You have an empty text area with a cursor in it.
:::
```

`type=code` — a code-writing exercise (code lives in `NOTE`):
```
:::task id=t1 type=code hint=180
Your first cylinder

NOTE
```python
import bpy
```

DONE WHEN
A cylinder appears in the 3D view.
:::
```

`type=answer` — self-observation with fill-in blanks. Write `{{name}}`
anywhere in `NOTE` (inline or in a table cell) for a text input the
student fills in themselves — nothing is graded, saved, or sent anywhere
(resets on reload, like `:::checklist`):
```
:::task id=t2 type=answer
Which number moves it up?

NOTE
| change | result |
|---|---|
| `location=(0,0,6)` | {{t2_z}} |

DONE WHEN
The blank is filled in.
:::
```

### `:::task id=… type=choice`
An **ungraded** multiple-choice warm-up — nothing saved server-side, a
student can click more than one option. `id` keeps option order stable
only, not tracked.
```
:::task id=q1 type=choice
Which one stores your name?

OPTIONS
- [x] `name = "Harel"` — Yes! Quotes = text.
- `name = Harel` — No quotes, so Python gets confused.
:::
```

---

## Layout / structure

### `:::journey`
A horizontal roadmap of stages. One `- ` line per stage:
`time/label | title | detail | now(optional)`.
```
:::journey
- Weeks 1–3 🐍 | Python | Mini-games | now
- Weeks 4–5 🎨 | Turtle + Games | Your own game
:::
```

### `:::figure caption="…"`
Preformatted ASCII art / small diagram, shown verbatim (monospace,
not run through markdown). `caption` optional.
```
:::figure caption="A branch is a right-angled triangle."
   🐍  ──▶  🎨  ──▶  💡
:::
```

### `:::objectives`
A numbered list of goals, each with an optional `CHECK` success line.
```
:::objectives
1. Make the computer do what you say.
CHECK — your family can't beat your guessing game.
:::
```

### `:::steps`
A plain numbered recap list — "what we covered", no `CHECK` line (compare `:::objectives`).
```
:::steps
1. Installed and opened Blender.
2. Found the Scripting tab.
3. Made a cylinder appear.
:::
```

### `:::grid`
Two (or more) side-by-side columns, split by a lone `---` line. Each
column's first line is its heading, plain lines (no `- ` prefix) after that.
```
:::grid
✅ YOU NEED
💻 Laptop
🎧 Headphones
---
🚫 YOU DON'T NEED
❌ Any install
:::
```

### `:::checklist`
A client-side, self-tick checklist — **not saved anywhere**, resets on
reload. No `id`, no server tracking (use `:::practice` for anything that
needs to persist).
```
:::checklist
- Zoom tested
- Cheat sheet printed
:::
```

---

## Quick decision guide

| I want… | use |
|---|---|
| a worked example / code demo | `:::example` |
| a warning or reminder | `:::tip` |
| reference material, setup steps | `:::card` |
| a definition or tangent | `:::aside` |
| a call-to-action banner | `:::push` |
| "here's why this formula holds" | `:::rule` |
| a question graded/tracked per student, code runs off-site | `:::practice` |
| a tracked instruction/checkbox step | `:::task type=step` |
| a tracked code-writing exercise | `:::task type=code` |
| a tracked fill-in-the-blank observation | `:::task type=answer` |
| an ungraded warm-up multiple-choice | `:::task type=choice` |
| a course/week roadmap | `:::journey` |
| ASCII art / a diagram | `:::figure` |
| goals still to reach, with success checks | `:::objectives` |
| a recap of what was already covered | `:::steps` |
| two-column comparison | `:::grid` |
| a self-tick, throwaway checklist | `:::checklist` |

# Build Prompt — Phase 2: lesson documents, timelines and themes

Paste this into Claude Code from the root of the existing student portal repo.

Two files must sit alongside this one and be read before any code is written:

- `FORMAT_SPEC.md` — the authoring format and theme tokens. This is the contract.
- `LESSON_TEMPLATE.md` — a working lesson using every construct in the spec. Your
  parser must handle this file completely, and it doubles as the test fixture.

---

## Context

I'm a freelance tutor with roughly 20 concurrent students across Fiverr, Preply
and direct Zoom. Subjects: Python, data science, computer vision, MATLAB,
Arduino/Webots robotics, Blender, exam prep. Ages 11 to postgraduate.

Phase 1 of this portal already exists and is deployed: student login, a dashboard,
courses with lessons, protected file downloads, per-lesson completion and a
progress bar. **Read the existing code before proposing anything.** I have made my
own changes since it was generated — work with what is in the repo, not with what
you would have written.

### The problem Phase 2 solves

Right now, for every student, I hand-write a Word document that is a dated log of
sessions. Each entry names a PowerPoint and pastes two or three Google Drive
links. Then I upload files to Drive, fix their sharing settings, copy the links,
and paste them in. That is 15–20 minutes per session before any teaching happens,
multiplied by 20 students.

Separately, my best teaching material is already interactive: a self-contained
HTML practice sheet with tasks, expected outputs, and full answers locked behind a
countdown timer. It works, students like it, but every one is hand-built HTML.

Phase 2 replaces both. I write one Markdown file per lesson. The portal turns it
into the interactive page, files it on the student's dated timeline, saves what
the student types, and shows me their answers before the next session.

---

## What to build

### 1. The lesson document

A `Lesson` gains a Markdown source field. Implement the parser exactly as
`FORMAT_SPEC.md` describes: YAML front matter with known and unknown keys, inline
blanks, `:::task` with four types, and the twelve `:::block` types.

Points that matter more than they look:

- **Unknown front matter keys go in a `JSONField` and render as header pills.**
  I must be able to add `topic: recursion` next month with no code change.
- **Task ids are explicit and stable.** Progress and answers key on them. Never
  key on position.
- **Re-parsing on save must not destroy progress.** Match by id; create what's new;
  mark removed tasks orphaned but never delete them, and warn me in the preview
  how many students have answers on them.
- **A task with no `SOLUTION` renders no hint button.** Some tasks exist so the
  student observes something. Offering a reveal destroys them.

### 2. Blanks and saved answers

Every `{{id}}` is an input whose value is saved per student. Save on blur and on a
debounce while typing. Show a quiet "Saved" indicator, not a modal.

Blanks are the reason this beats a file: I need to see what the student wrote.

### 3. The timer

Port the timing behaviour from the existing practice sheet. Press "I'm stuck", a
countdown with a filling ring runs, the solution appears when it hits zero. **No
skip button.** The waiting is the pedagogy and it has been tested with real
students.

Default 120 seconds, `hint_seconds` per lesson, `hint=` per task. **Log every
reveal**, with a timestamp, against the student.

### 4. The dated timeline

This is what replaces my Word document.

Each student's course page becomes a reverse-chronological list of dated entries.
Three kinds:

- **Lesson entries** — a parsed Markdown document, opens into the interactive page
- **File entries** — existing `.pptx`, `.ipynb`, `.csv`, `.pdf` attached to a date,
  download only, nothing parsed
- **Note entries** — a date and one line of text, nothing else

The note entry is not optional. My current document has days that say only "We did
practice of previous project." Without note entries I would have to keep the Word
file alive alongside the portal, which defeats the point.

One entry may hold both a Markdown lesson and attached files.

The course also needs a pinned resources area, above the timeline and not tied to
a date, for the study plan and folder links that currently sit at the top of my
document.

### 5. Three themes

`kids`, `beginner`, `professional`. Tokens and flags are in `FORMAT_SPEC.md`.

**One set of templates. CSS custom properties plus a small number of flags.** Do
not create three template directories — if adding a fourth theme is not roughly a
40-line stylesheet addition, the implementation is wrong.

Theme is set on the student, overridable per lesson.

`beginner` must match the existing practice sheet closely enough that it looks
like the same product. That file is the approved house style.

### 6. Getting content in

Three routes, all through the Django admin, all landing on a dated entry:

1. **Paste** — a textarea with a live preview beside it. This will be the common
   case: I generate the lesson in a chat and paste it. Make this path fast.
2. **Upload** a `.md` file — same preview.
3. **Attach** existing files — no parsing, just downloads on the entry.

Every route shows a preview before saving: student, date, theme, task count, blank
count, warnings, and the rendered body. **Nothing saves without my confirmation.**

Prefilling the form by reading a filename like `Andy_W3D2_TableToModel.pptx` is
welcome. Filing silently on a guess is not — a misfiled lesson means one child's
material appearing under another child's login.

After saving, the Markdown stays editable in the admin, with the same preview.
Mid-session fixes need to take seconds.

### 7. The tutor view

Per student, per lesson: every saved blank, every checkbox, which tasks were
completed, and which solutions were revealed and when.

The reveal log is the most valuable thing here. It tells me where a student
actually struggled, which a completion percentage does not.

---

## Constraints

**Stack** — unchanged from Phase 1: Django, Django admin, HTMX, Alpine, Tailwind,
SQLite, PythonAnywhere. Please don't re-litigate it. Keep dependencies minimal; I
maintain this alone. A Markdown library and a YAML parser are expected; a
heavyweight CMS or a JS build step is not.

**Security** — carried forward and non-negotiable. Several students are minors,
some in the EU.

- Students never see each other's lessons, answers or files
- All enrolment filtering stays in `learning/services.py`; views must not build
  their own querysets
- Uploads stay outside the web root, served only through the permission-checking
  view
- `:::raw` is sanitised with a strict allowlist: no `<script>`, no `on*`
  attributes, no arbitrary `<iframe>`
- Front matter can never inject CSS or HTML. `accent` accepts a hex colour and
  nothing else
- Secrets stay in environment variables; the repo stays private

**Practical**

- Mobile-first. Students check work on phones, and the `kids` theme especially
  will be read on a phone.
- Respect `prefers-reduced-motion`. Keyboard focus must stay visible.
- Extend the existing test suite. It already asserts cross-student isolation —
  add: parsing `LESSON_TEMPLATE.md` end to end, progress surviving a re-parse with
  reordered tasks, and one student being unable to read another's saved answers.

---

## How to work

Build in this order, stopping after each for me to look:

1. **Parser plus renderer, `beginner` theme only.** Success: I paste
   `LESSON_TEMPLATE.md` and get a working page — timers, blanks, tasks, all blocks.
2. **Saved answers, the reveal log and the tutor view.**
3. **The dated timeline**, with all three entry kinds and pinned resources.
4. **The `kids` and `professional` themes.**

Ask me when something is ambiguous rather than guessing. Tell me directly if part
of this plan is wrong — I would rather hear it now than after it is built.

Explain any decision that will be hard to reverse, particularly around how tasks
and answers are keyed, since that is where student data gets orphaned.

---

## Success criteria

I paste a Markdown lesson into the admin, confirm the preview, and a student logs
in on a phone to find it on their timeline under the right date. They fill in
blanks, wait out a timer on one task, tick two others complete, and close the tab.
I open the tutor view and read exactly what they wrote and where they got stuck.

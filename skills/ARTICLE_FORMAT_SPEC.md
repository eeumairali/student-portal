# Article (domain tutorial) format specification

One authoring format for every public article/tutorial page: **plain
Markdown with YAML front matter**. This is a different, much simpler
system than lessons — see `FORMAT_SPEC.md` for that one. Do not mix the
two up: lesson `:::example` / `:::practice` / `:::task` / etc. block
constructs **do not exist here** and will render as literal text.

**This file is the single source of truth for what article pages can
render.** The renderer is the stock Python `markdown` library with three
extensions — nothing else is parsed. If content needs something outside
that (syntax highlighting, admonitions, footnotes, definition lists,
anything `:::`-fenced), it will not render as intended.

---

## 1. Front matter

```yaml
---
domain: Python                 # required — category; created if missing
title: My new tutorial         # required
summary: A short one-line description shown on cards and search results.   # optional
slug: my-new-tutorial          # optional — auto-derived from title if omitted
order: 1                        # optional — sort position within its domain, default 1
visible: true                   # optional — default true; false hides it from the public site
---
```

Every key is known — there is no `meta`/unknown-key pass-through like
lessons have. Extra keys in front matter are silently ignored.

### Validation

- Missing `domain` or `title` → reject, "The document needs both domain:
  and title: in its front matter."
- No front matter block at all → warning: "No front matter found — the
  file must start with a `---` block naming domain: and title:."
- Front matter that isn't valid YAML, or isn't a mapping → warning, and
  front matter is treated as empty (so the required-field error above
  still fires).
- `domain` is matched case-insensitively against existing domains and
  created automatically if new — never rejected for "unknown domain".
- Matching an existing article to update instead of creating a
  duplicate, in order: `slug` (if given) → exact `title` + `domain`
  match. If a match is found without an explicit edit target, the
  preview warns "An article with this domain and title already exists —
  it will be updated, not duplicated."

---

## 2. Body

Everything after the closing `---` of the front matter is the article
body — **plain Markdown, no block-level constructs at all.** There is no
`## `-per-block numbering, no numbered steps, no colored panels. Structure
it with ordinary Markdown headings.

Rendered with `markdown.markdown(body, extensions=["tables",
"fenced_code", "sane_lists", "codehilite"])`
(`tutorials/models.py:render_markdown`). That means:

**Supported:**
- Headings (`#`, `##`, …), paragraphs, **bold**, *italic*, links
- Blockquotes, inline `code`
- Fenced code blocks with **syntax highlighting** (` ```python ... ``` `)
  — name the language right after the opening fence (`python`, `js`,
  `bash`, `json`, …) to get it colored via Pygments; an unlabeled fence
  still renders as plain code, no error
- Pipe tables (`tables` extension)
- Ordered and unordered lists, including nested ones (`sane_lists`
  extension — stricter than default: a list only continues if its marker
  style is consistent)

**Not supported** (will render as literal text or be silently dropped):
- Any `:::name` block (`:::example`, `:::tip`, `:::practice`, `:::task`,
  `:::journey`, `:::figure`, `:::objectives`, `:::steps`, `:::grid`,
  `:::push`, `:::card`, `:::aside`, `:::rule`, `:::checklist`) — those are
  lesson-only
- Footnotes, definition lists, `attr_list`, table of contents, admonitions
  — any `markdown` extension not in `MD_EXTENSIONS`
- Practice questions, hint timers, per-student progress tracking of any
  kind — articles are static public pages, not tied to a student

If you need a numbered walkthrough or a callout panel, write it as plain
Markdown (a numbered list, a blockquote) rather than inventing a
`:::`-style block — the parser will not special-case it.

---

## 3. Worked example

```markdown
---
domain: Python
title: My new tutorial
summary: A short one-line description shown on cards and search results.
visible: true
---

## Getting started

Write your tutorial here in Markdown — headings with `##`, **bold**, `code`,
and fenced code blocks all work.

```python
print("hello world")
```

## A quick reference

| function | what it does |
|---|---|
| `print()` | writes text to the console |
| `len()` | counts items in a list or string |
```

---

## 4. Parsing and storage

**Parse on save, store the body only.** `tutorials/article_editor.py`
splits front matter from body (`parse_article`); `tutorials/article_save.py`
resolves a save plan and then writes a `Tutorial` row — `domain`, `title`,
`slug`, `summary`, `order`, `is_published` come from front matter, `body`
is the raw Markdown (parsed to HTML at render time, not stored as HTML).
There is no separate model for sub-parts of an article — one `Tutorial`
row is the whole page.

**Preview before commit.** Every paste/upload shows the parsed front
matter, any warnings, and the rendered HTML body. Nothing saves until the
tutor confirms with `action=confirm`.

---

## 5. Adapting existing content with AI

Give an AI the source content plus this file, and ask it to produce
front matter (`domain`, `title`, `summary`) followed by plain Markdown —
headings, prose, code fences, tables, lists only. **Before generating any
article markdown, confirm the source doesn't need lesson-only constructs
(practice questions, tip panels, journeys, etc.)** — if it does, that
content belongs in `FORMAT_SPEC.md`'s lesson format instead, not here. If
the source needs something neither format supports (e.g. an embedded
video, syntax highlighting), say so explicitly rather than inventing
markup this renderer will not understand.

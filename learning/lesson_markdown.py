"""Parses the lesson Markdown format described in skills/FORMAT_SPEC.md into a
tree of render-ready nodes. See skills/LESSON_TEMPLATE.md for a worked example
of every construct handled here.

Nothing in this module touches the database — it is pure text in, node tree
out, so it can be reused for the admin preview and for the real save path.
"""
from __future__ import annotations

import html
import re
from dataclasses import dataclass, field
from datetime import date as date_cls

import bleach
import markdown as md
import yaml
from bleach.css_sanitizer import CSSSanitizer

KNOWN_FRONT_MATTER_KEYS = {
    "student", "date", "title", "subtitle", "course",
    "theme", "hint_seconds", "visible", "time", "duration", "accent",
}
THEMES = {"kids", "beginner", "professional"}
TASK_TYPES = {"code", "choice", "step", "answer"}
RUNNABLE_LANGS = {"python"}

MD_EXTENSIONS = ["tables", "fenced_code", "sane_lists"]

BLANK_RE = re.compile(r"\{\{([a-zA-Z][a-zA-Z0-9_]*)(?:\|(wide|long))?\}\}")
FRONT_MATTER_RE = re.compile(r"^---\s*\n(.*?\n)---[ \t]*\n?(.*)$", re.DOTALL)
BLOCK_OPEN_RE = re.compile(r"^:::(\S+)(.*)$")
HEADING_RE = re.compile(r"^(#{1,3})\s+(.*)$")
KEYWORD_RE = re.compile(r"^(NOTE|EXPECTED|DONE WHEN|SOLUTION|OPTIONS|STARTER)\s*$")
FENCE_STRIP_RE = re.compile(r"^```[^\n]*\n(.*?)\n?```\s*$", re.DOTALL)
NUMBERED_RE = re.compile(r"^\d+\.\s+(.*)$")
WHY_RE = re.compile(r"^WHY\s*[—-]\s*(.*)$")
CHECK_RE = re.compile(r"^CHECK\s*[—-]\s*(.*)$")
OPTION_RE = re.compile(r"^-\s*(\[x\]\s*)?(.*)$")
HEX_COLOUR_RE = re.compile(r"^#[0-9a-fA-F]{3}([0-9a-fA-F]{3})?$")

ALLOWED_RAW_TAGS = [
    "p", "br", "strong", "em", "b", "i", "u", "span", "div", "ul", "ol", "li",
    "a", "code", "pre", "blockquote", "table", "thead", "tbody", "tr", "th", "td",
    "h1", "h2", "h3", "h4", "img", "hr",
]
ALLOWED_RAW_ATTRS = {
    "a": ["href", "title"],
    "img": ["src", "alt", "title"],
    "*": ["class", "style"],
}
ALLOWED_RAW_CSS_PROPERTIES = [
    "color", "background-color", "text-align", "font-weight", "font-style",
    "font-size", "margin", "margin-top", "margin-bottom", "padding", "text-decoration",
]
_css_sanitizer = CSSSanitizer(allowed_css_properties=ALLOWED_RAW_CSS_PROPERTIES)


# ---------------------------------------------------------------- rendering --

def render_markdown(text: str) -> str:
    text = text.strip("\n")
    return md.markdown(text, extensions=MD_EXTENSIONS) if text.strip() else ""


def substitute_blanks(html_text: str) -> tuple[str, list[str]]:
    ids: list[str] = []

    def repl(m: re.Match) -> str:
        blank_id, variant = m.group(1), m.group(2)
        ids.append(blank_id)
        if variant == "long":
            return (
                f'<textarea class="blank blank-long" data-blank-id="{blank_id}" '
                f'rows="3" aria-label="Your answer"></textarea>'
            )
        cls = "blank blank-wide" if variant == "wide" else "blank"
        return (
            f'<input type="text" class="{cls}" data-blank-id="{blank_id}" '
            f'autocomplete="off" aria-label="Your answer">'
        )

    return BLANK_RE.sub(repl, html_text), ids


def render_with_blanks(text: str) -> tuple[str, list[str]]:
    return substitute_blanks(render_markdown(text))


def render_inline(text: str) -> tuple[str, list[str]]:
    """Like render_with_blanks, but unwraps a single enclosing <p> so the
    result can sit inside a heading, label or list item."""
    html_out, ids = render_with_blanks(text)
    stripped = html_out.strip()
    if stripped.startswith("<p>") and stripped.endswith("</p>") and stripped.count("<p>") == 1:
        stripped = stripped[3:-4]
    return stripped, ids


def sanitize_raw(text: str) -> str:
    return bleach.clean(
        text.strip("\n"),
        tags=ALLOWED_RAW_TAGS,
        attributes=ALLOWED_RAW_ATTRS,
        protocols=["http", "https", "mailto"],
        css_sanitizer=_css_sanitizer,
        strip=True,
    )


# --------------------------------------------------------------------- nodes --

@dataclass
class Prose:
    html: str
    template_name: str = "learning/lesson/blocks/prose.html"


@dataclass
class Heading:
    eyebrow: str | None
    title: str
    template_name: str = "learning/lesson/blocks/heading.html"


@dataclass
class Tip:
    html: str
    template_name: str = "learning/lesson/blocks/tip.html"


@dataclass
class Card:
    title: str
    html: str
    template_name: str = "learning/lesson/blocks/card.html"


@dataclass
class RuleColumn:
    label: str
    html: str


@dataclass
class Rule:
    title: str
    columns: list[RuleColumn]
    template_name: str = "learning/lesson/blocks/rule.html"


@dataclass
class Steps:
    items: list[str]
    template_name: str = "learning/lesson/blocks/steps.html"


@dataclass
class Grid:
    columns: list[RuleColumn]
    template_name: str = "learning/lesson/blocks/grid.html"


@dataclass
class Figure:
    caption: str
    text: str
    template_name: str = "learning/lesson/blocks/figure.html"


@dataclass
class Objective:
    text: str
    why: str
    check: str


@dataclass
class Objectives:
    items: list[Objective]
    template_name: str = "learning/lesson/blocks/objectives.html"


@dataclass
class JourneyItem:
    label: str
    focus: str
    outcome: str
    state: str | None


@dataclass
class Journey:
    items: list[JourneyItem]
    template_name: str = "learning/lesson/blocks/journey.html"


@dataclass
class Aside:
    title: str
    html: str
    template_name: str = "learning/lesson/blocks/aside.html"


@dataclass
class Push:
    title: str
    html: str
    template_name: str = "learning/lesson/blocks/push.html"


@dataclass
class ChecklistItem:
    index: int
    check_id: str
    html: str


@dataclass
class Checklist:
    items: list[ChecklistItem]
    template_name: str = "learning/lesson/blocks/checklist.html"


@dataclass
class Raw:
    html: str
    template_name: str = "learning/lesson/blocks/raw.html"


@dataclass
class ChoiceOption:
    html: str
    correct: bool
    feedback_html: str


@dataclass
class Task:
    task_id: str
    type: str
    hint_seconds: int | None
    title: str
    note: list
    body: list
    expected: str | None
    done_when_html: str | None
    solution: list | None
    options: list[ChoiceOption]
    has_solution: bool
    runnable: str | None = None
    starter_code: str = ""
    template_name: str = "learning/lesson/blocks/task.html"


@dataclass
class ParsedLesson:
    front_matter: dict
    meta: dict
    nodes: list
    tasks: list[Task]
    blank_ids: list[str]
    warnings: list[str]

    @property
    def theme(self) -> str:
        return self.front_matter.get("theme") or "beginner"

    @property
    def hint_seconds_default(self) -> int:
        try:
            return int(self.front_matter.get("hint_seconds") or 30)
        except (TypeError, ValueError):
            return 30

    def task_count(self) -> int:
        return len(self.tasks)

    def blank_count(self) -> int:
        return len(self.blank_ids)


# ------------------------------------------------------------------- parsing --

def parse_lesson(raw_text: str) -> ParsedLesson:
    warnings: list[str] = []
    raw_text = raw_text.lstrip("﻿")
    m = FRONT_MATTER_RE.match(raw_text)
    if not m:
        warnings.append("No front matter found — the file must start with a `---` block.")
        fm_raw, body_text = "", raw_text
    else:
        fm_raw, body_text = m.group(1), m.group(2)

    body_text = re.sub(r"<!--.*?-->", "", body_text, flags=re.DOTALL)

    try:
        fm_data = yaml.safe_load(fm_raw) or {}
    except yaml.YAMLError as e:
        warnings.append(f"Front matter is not valid YAML: {e}")
        fm_data = {}
    if not isinstance(fm_data, dict):
        warnings.append("Front matter must be a mapping of key: value pairs.")
        fm_data = {}

    front_matter: dict = {}
    meta: dict = {}
    for key, value in fm_data.items():
        if key in KNOWN_FRONT_MATTER_KEYS:
            front_matter[key] = value
        else:
            meta[key] = value

    for required in ("student", "date", "title"):
        if not front_matter.get(required):
            warnings.append(f"Missing required field: {required}")

    date_value = front_matter.get("date")
    if date_value is not None and not isinstance(date_value, date_cls):
        warnings.append(f"date must be YYYY-MM-DD, got: {date_value!r}")

    theme = front_matter.get("theme")
    if theme and theme not in THEMES:
        warnings.append(f"Unknown theme: {theme!r} — expected kids, beginner or professional.")
        front_matter["theme"] = None

    accent = front_matter.get("accent")
    if accent and not HEX_COLOUR_RE.match(str(accent)):
        warnings.append(f"accent must be a hex colour like #F4845F, got: {accent!r} — ignored.")
        front_matter["accent"] = None

    tasks: list[Task] = []
    all_blank_ids: list[str] = []
    nodes = parse_body(body_text, tasks, all_blank_ids, warnings)

    seen_ids: dict[str, int] = {}
    for t in tasks:
        seen_ids[t.task_id] = seen_ids.get(t.task_id, 0) + 1
    dupes = [tid for tid, n in seen_ids.items() if n > 1]
    if dupes:
        warnings.append("Duplicate task id(s), only the last will keep progress correctly: " + ", ".join(dupes))

    return ParsedLesson(front_matter, meta, nodes, tasks, all_blank_ids, warnings)


def parse_attrs(attr_str: str) -> dict:
    attrs = {}
    for m in re.finditer(r'(\w+)=("([^"]*)"|\'([^\']*)\'|(\S+))', attr_str):
        key = m.group(1)
        val = m.group(3) if m.group(3) is not None else (m.group(4) if m.group(4) is not None else m.group(5))
        attrs[key] = val
    return attrs


def split_fences(text: str):
    """Yield ('text', content) for plain runs and ('block', name, attrs, content)
    for ':::name ... :::' fences. One level of ':::' nesting inside a fence is
    kept verbatim in its content for the caller to re-parse."""
    lines = text.split("\n")
    i, n = 0, len(lines)
    buf: list[str] = []
    while i < n:
        stripped = lines[i].strip()
        m = BLOCK_OPEN_RE.match(stripped) if stripped != ":::" else None
        if m:
            if buf:
                yield ("text", None, None, "\n".join(buf))
                buf = []
            name, attr_str = m.group(1), m.group(2)
            depth = 1
            j = i + 1
            inner: list[str] = []
            while j < n:
                s2 = lines[j].strip()
                if BLOCK_OPEN_RE.match(s2) and s2 != ":::":
                    depth += 1
                elif s2 == ":::":
                    depth -= 1
                    if depth == 0:
                        break
                inner.append(lines[j])
                j += 1
            yield ("block", name, parse_attrs(attr_str), "\n".join(inner))
            i = j + 1
        else:
            buf.append(lines[i])
            i += 1
    if buf:
        yield ("text", None, None, "\n".join(buf))


def parse_body(text: str, tasks: list, all_blank_ids: list, warnings: list) -> list:
    nodes = []
    for kind, name, attrs, content in split_fences(text):
        if kind == "text":
            nodes.extend(parse_text_chunk(content, all_blank_ids))
        else:
            node = build_block(name, attrs, content, tasks, all_blank_ids, warnings)
            if node is not None:
                nodes.append(node)
    return nodes


FENCE_RE = re.compile(r"^(```|~~~)")


def parse_text_chunk(text: str, all_blank_ids: list) -> list:
    """Split a run of plain text into Heading + Prose nodes. A heading whose
    text contains an em dash splits into an eyebrow label and a title.
    Lines inside a fenced code block are never read as headings — a Python
    comment like ``# clear the scene`` is not a section title."""
    nodes = []
    buf: list[str] = []
    in_fence = False

    def flush():
        chunk = "\n".join(buf).strip("\n")
        buf.clear()
        if chunk.strip():
            html_out, ids = render_with_blanks(chunk)
            all_blank_ids.extend(ids)
            nodes.append(Prose(html_out))

    for line in text.split("\n"):
        if FENCE_RE.match(line.strip()):
            in_fence = not in_fence
            buf.append(line)
            continue
        if not in_fence:
            m = HEADING_RE.match(line.strip())
            if m:
                flush()
                heading_text = m.group(2)
                if "—" in heading_text:
                    eyebrow, title = heading_text.split("—", 1)
                    nodes.append(Heading(eyebrow.strip(), title.strip()))
                else:
                    nodes.append(Heading(None, heading_text.strip()))
                continue
        buf.append(line)
    flush()
    return nodes


def parse_columns(content: str, all_blank_ids: list) -> list[RuleColumn]:
    columns: list[RuleColumn] = []
    current: list[str] = []

    def flush():
        if not current:
            return
        label = current[0].strip()
        body = "\n".join(current[1:]).strip("\n")
        if body.strip():
            html_out, ids = render_with_blanks(body)
            all_blank_ids.extend(ids)
        else:
            html_out = ""
        columns.append(RuleColumn(label, html_out))

    for line in content.split("\n"):
        if line.strip() == "---":
            flush()
            current.clear()
        else:
            current.append(line)
    flush()
    return columns


def parse_numbered_items(content: str) -> list[str]:
    items = []
    for line in content.split("\n"):
        m = NUMBERED_RE.match(line.strip())
        if m:
            items.append(m.group(1))
    return items


def parse_objectives(content: str, all_blank_ids: list) -> list[Objective]:
    raw_items = []
    current = None
    for raw_line in content.split("\n"):
        line = raw_line.strip()
        if not line:
            continue
        m = NUMBERED_RE.match(line)
        if m:
            if current:
                raw_items.append(current)
            current = {"text": m.group(1), "why": "", "check": ""}
            continue
        m = WHY_RE.match(line)
        if m and current is not None:
            current["why"] = m.group(1)
            continue
        m = CHECK_RE.match(line)
        if m and current is not None:
            current["check"] = m.group(1)
            continue
    if current:
        raw_items.append(current)

    result = []
    for it in raw_items:
        text_html, ids1 = render_inline(it["text"])
        why_html, ids2 = render_inline(it["why"]) if it["why"] else ("", [])
        check_html, ids3 = render_inline(it["check"]) if it["check"] else ("", [])
        all_blank_ids.extend(ids1 + ids2 + ids3)
        result.append(Objective(text_html, why_html, check_html))
    return result


def parse_journey(content: str, all_blank_ids: list) -> list[JourneyItem]:
    items = []
    for raw_line in content.split("\n"):
        line = raw_line.strip()
        if not line.startswith("-"):
            continue
        line = line[1:].strip()
        parts = [p.strip() for p in line.split("|")]
        while len(parts) < 3:
            parts.append("")
        label, focus, outcome = parts[0], parts[1], parts[2]
        state = parts[3].strip() if len(parts) > 3 else ""
        if state not in ("now", "done"):
            state = None
        label_html, i1 = render_inline(label)
        focus_html, i2 = render_inline(focus)
        outcome_html, i3 = render_inline(outcome)
        all_blank_ids.extend(i1 + i2 + i3)
        items.append(JourneyItem(label_html, focus_html, outcome_html, state))
    return items


def parse_checklist(content: str, all_blank_ids: list) -> list[ChecklistItem]:
    items = []
    idx = 0
    for raw_line in content.split("\n"):
        line = raw_line.strip()
        if not line.startswith("-"):
            continue
        idx += 1
        text = line[1:].strip()
        html_out, ids = render_inline(text)
        all_blank_ids.extend(ids)
        items.append(ChecklistItem(idx, f"check_{idx}", html_out))
    return items


def parse_choice_options(content: str, all_blank_ids: list) -> list[ChoiceOption]:
    options = []
    for raw_line in content.split("\n"):
        line = raw_line.strip()
        if not line.startswith("-"):
            continue
        m = OPTION_RE.match(line)
        if not m:
            continue
        correct = bool(m.group(1))
        rest = m.group(2)
        if "—" in rest:
            opt_text, feedback = rest.split("—", 1)
        else:
            opt_text, feedback = rest, ""
        opt_html, i1 = render_inline(opt_text.strip())
        fb_html, i2 = render_inline(feedback.strip()) if feedback.strip() else ("", [])
        all_blank_ids.extend(i1 + i2)
        options.append(ChoiceOption(opt_html, correct, fb_html))
    return options


def split_task_sections(text: str) -> dict:
    sections: dict = {None: []}
    current = None
    for line in text.split("\n"):
        m = KEYWORD_RE.match(line.strip())
        if m:
            current = m.group(1)
            sections.setdefault(current, [])
            continue
        sections.setdefault(current, []).append(line)
    return {k: "\n".join(v) for k, v in sections.items()}


def extract_starter_code(text: str) -> str:
    """STARTER holds literal code, not markdown — a ```fenced``` block or,
    failing that, the raw lines as-is, so the tutor never has to think about
    escaping it."""
    stripped = text.strip("\n")
    m = FENCE_STRIP_RE.match(stripped)
    return m.group(1) if m else stripped


def build_task(attrs: dict, content: str, tasks: list, all_blank_ids: list, warnings: list) -> Task:
    task_id = attrs.get("id")
    if not task_id:
        task_id = f"task_{len(tasks) + 1}"
        warnings.append(f"A :::task block is missing id= — assigned a temporary id ({task_id}).")

    task_type = attrs.get("type", "code")
    if task_type not in TASK_TYPES:
        warnings.append(f"Task {task_id}: unknown type '{task_type}', treating as 'code'.")
        task_type = "code"

    hint_seconds = None
    hint_raw = attrs.get("hint")
    if hint_raw is not None:
        try:
            hint_seconds = int(hint_raw)
        except ValueError:
            warnings.append(f"Task {task_id}: hint= must be a whole number of seconds, got {hint_raw!r}.")

    lines = content.split("\n")
    idx = 0
    while idx < len(lines) and not lines[idx].strip():
        idx += 1
    title_line = lines[idx].strip() if idx < len(lines) else ""
    title_html, ids = render_inline(title_line)
    all_blank_ids.extend(ids)
    rest = "\n".join(lines[idx + 1:])

    sections = split_task_sections(rest)
    body_nodes = parse_body(sections.get(None, ""), tasks, all_blank_ids, warnings)

    note_nodes = []
    if sections.get("NOTE", "").strip():
        note_nodes = parse_body(sections["NOTE"], tasks, all_blank_ids, warnings)

    expected = None
    if sections.get("EXPECTED", "").strip():
        expected = sections["EXPECTED"].strip()

    done_when_html = None
    if sections.get("DONE WHEN", "").strip():
        done_when_html, ids = render_inline(sections["DONE WHEN"])
        all_blank_ids.extend(ids)

    has_solution = bool(sections.get("SOLUTION", "").strip())
    solution_nodes = parse_body(sections["SOLUTION"], tasks, all_blank_ids, warnings) if has_solution else None

    options: list[ChoiceOption] = []
    if sections.get("OPTIONS", "").strip():
        options = parse_choice_options(sections["OPTIONS"], all_blank_ids)
        if task_type != "choice":
            warnings.append(f"Task {task_id}: has an OPTIONS section but type is '{task_type}', not 'choice'.")
    elif task_type == "choice":
        warnings.append(f"Task {task_id}: type is 'choice' but has no OPTIONS section.")

    runnable = attrs.get("runnable")
    if runnable is not None:
        if task_type != "code":
            warnings.append(f"Task {task_id}: runnable= only applies to type=code, ignored.")
            runnable = None
        elif runnable not in RUNNABLE_LANGS:
            warnings.append(f"Task {task_id}: runnable='{runnable}' isn't supported yet (only python), ignored.")
            runnable = None

    starter_code = extract_starter_code(sections["STARTER"]) if sections.get("STARTER", "").strip() else ""

    task = Task(
        task_id=task_id, type=task_type, hint_seconds=hint_seconds,
        title=title_html, note=note_nodes, body=body_nodes,
        expected=expected, done_when_html=done_when_html,
        solution=solution_nodes, options=options, has_solution=has_solution,
        runnable=runnable, starter_code=starter_code,
    )
    tasks.append(task)
    return task


def build_block(name: str, attrs: dict, content: str, tasks: list, all_blank_ids: list, warnings: list):
    if name == "task":
        return build_task(attrs, content, tasks, all_blank_ids, warnings)
    if name == "tip":
        html_out, ids = render_inline(content)
        all_blank_ids.extend(ids)
        return Tip(html_out)
    if name == "card":
        html_out, ids = render_with_blanks(content)
        all_blank_ids.extend(ids)
        return Card(attrs.get("title", ""), html_out)
    if name == "rule":
        return Rule(attrs.get("title", ""), parse_columns(content, all_blank_ids))
    if name == "grid":
        return Grid(parse_columns(content, all_blank_ids))
    if name == "steps":
        items = []
        for item_text in parse_numbered_items(content):
            html_out, ids = render_inline(item_text)
            all_blank_ids.extend(ids)
            items.append(html_out)
        return Steps(items)
    if name == "figure":
        return Figure(attrs.get("caption", ""), html.escape(content.strip("\n")))
    if name == "objectives":
        return Objectives(parse_objectives(content, all_blank_ids))
    if name == "journey":
        return Journey(parse_journey(content, all_blank_ids))
    if name == "aside":
        html_out, ids = render_with_blanks(content)
        all_blank_ids.extend(ids)
        return Aside(attrs.get("title", ""), html_out)
    if name == "push":
        html_out, ids = render_with_blanks(content)
        all_blank_ids.extend(ids)
        return Push(attrs.get("title", ""), html_out)
    if name == "checklist":
        return Checklist(parse_checklist(content, all_blank_ids))
    if name == "raw":
        return Raw(sanitize_raw(content))

    warnings.append(f"Unknown block type :::{name} — rendered as plain text so nothing is lost.")
    html_out, ids = render_with_blanks(content)
    all_blank_ids.extend(ids)
    return Card(f"Unrecognised block: {name}", html_out)

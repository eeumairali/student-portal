"""Parses the simplified lesson Markdown format described in
skills/FORMAT_SPEC.md into a tree of render-ready nodes. See
skills/LESSON_TEMPLATE.md for a worked example.

Nothing in this module touches the database — it is pure text in, node tree
out, so it can be reused for the admin preview and for the real save path.

Front matter, then a sequence of ``## `` blocks (auto-numbered "N of TOTAL"),
each holding prose and any mix of: ``:::example``, ``:::tip``, ``:::practice``
(a question worked out on the student's own computer, with hint/solution
reveal), ``:::task ... type=choice`` (an ungraded multiple-choice warm-up),
``:::journey``, ``:::figure``, ``:::objectives``, ``:::grid``, ``:::push``,
and ``:::checklist``. See skills/FORMAT_SPEC.md for the exact syntax of each
— that file is the single source of truth; don't invent new block names.
There is still no in-browser code execution.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date as date_cls

import markdown as md
import yaml

KNOWN_FRONT_MATTER_KEYS = {
    "student", "date", "title", "subtitle", "course",
    "topics", "hint_seconds", "visible", "accent",
}
MD_EXTENSIONS = ["tables", "fenced_code", "sane_lists"]

FRONT_MATTER_RE = re.compile(r"^---\s*\n(.*?\n)---[ \t]*\n?(.*)$", re.DOTALL)
BLOCK_OPEN_RE = re.compile(r"^:::(\S+)(.*)$")
BLOCK_HEADING_RE = re.compile(r"^##\s+(.*)$")
KEYWORD_RE = re.compile(r"^(EXPECTED|SOLUTION)\s*$")
HEX_COLOUR_RE = re.compile(r"^#[0-9a-fA-F]{3}([0-9a-fA-F]{3})?$")
FENCE_RE = re.compile(r"^(```|~~~)")


# ---------------------------------------------------------------- rendering --

def render_markdown(text: str) -> str:
    text = text.strip("\n")
    return md.markdown(text, extensions=MD_EXTENSIONS) if text.strip() else ""


# --------------------------------------------------------------------- nodes --

@dataclass
class Prose:
    html: str
    template_name: str = "learning/lesson/blocks/prose.html"


@dataclass
class Example:
    html: str
    template_name: str = "learning/lesson/blocks/example.html"


@dataclass
class Tip:
    html: str
    template_name: str = "learning/lesson/blocks/tip.html"


@dataclass
class Journey:
    """A horizontal roadmap of stages. See :::journey in FORMAT_SPEC.md."""

    steps: list
    template_name: str = "learning/lesson/blocks/journey.html"


@dataclass
class Figure:
    """Preformatted ASCII art / diagram with an optional caption."""

    caption: str
    art: str
    template_name: str = "learning/lesson/blocks/figure.html"


@dataclass
class Objectives:
    """A numbered list of goals, each with an optional CHECK success line."""

    items: list
    template_name: str = "learning/lesson/blocks/objectives.html"


@dataclass
class Grid:
    """Two (or more) side-by-side columns, split by a lone `---` line."""

    columns: list
    template_name: str = "learning/lesson/blocks/grid.html"


@dataclass
class Push:
    """A callout / call-to-action panel with a title and markdown body."""

    title: str
    html: str
    template_name: str = "learning/lesson/blocks/push.html"


@dataclass
class Checklist:
    """A self-check list the student can tick off (not saved to the server —
    purely a client-side memory aid, unlike :::practice)."""

    items: list
    template_name: str = "learning/lesson/blocks/checklist.html"


@dataclass
class Quiz:
    """An ungraded multiple-choice warm-up question. Each option carries its
    own feedback, shown when clicked — nothing is saved server-side."""

    quiz_id: str
    question_html: str
    options: list
    template_name: str = "learning/lesson/blocks/quiz.html"


@dataclass
class Practice:
    """One self-practice question. The student writes/runs the code on their
    own computer, not on the site — the site only holds the prompt, the
    expected result to self-check against, and a timed hint reveal."""

    practice_id: str
    index: int
    hint_seconds: int | None
    question_html: str
    expected: str | None
    solution_html: str | None
    has_solution: bool
    template_name: str = "learning/lesson/blocks/practice.html"


@dataclass
class Block:
    title: str
    index: int
    total: int
    nodes: list
    template_name: str = "learning/lesson/blocks/block.html"


@dataclass
class ParsedLesson:
    front_matter: dict
    meta: dict
    topics: list[str]
    blocks: list[Block]
    practices: list[Practice]
    quizzes: list[Quiz]
    warnings: list[str]

    @property
    def hint_seconds_default(self) -> int:
        try:
            return int(self.front_matter.get("hint_seconds") or 20)
        except (TypeError, ValueError):
            return 20

    def practice_count(self) -> int:
        return len(self.practices)


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

    accent = front_matter.get("accent")
    if accent and not HEX_COLOUR_RE.match(str(accent)):
        warnings.append(f"accent must be a hex colour like #F4845F, got: {accent!r} — ignored.")
        front_matter["accent"] = None

    topics = front_matter.get("topics") or []
    if isinstance(topics, str):
        topics = [topics]
    if not isinstance(topics, list):
        warnings.append(f"topics must be a list, got: {topics!r} — ignored.")
        topics = []
    front_matter["topics"] = [str(t) for t in topics]

    practices: list[Practice] = []
    quizzes: list[Quiz] = []
    blocks = parse_blocks(body_text, practices, quizzes, warnings)

    seen_ids: dict[str, int] = {}
    for p in practices:
        seen_ids[p.practice_id] = seen_ids.get(p.practice_id, 0) + 1
    dupes = [pid for pid, n in seen_ids.items() if n > 1]
    if dupes:
        warnings.append("Duplicate practice id(s), only the last will keep progress correctly: " + ", ".join(dupes))

    seen_quiz_ids: dict[str, int] = {}
    for q in quizzes:
        seen_quiz_ids[q.quiz_id] = seen_quiz_ids.get(q.quiz_id, 0) + 1
    quiz_dupes = [qid for qid, n in seen_quiz_ids.items() if n > 1]
    if quiz_dupes:
        warnings.append("Duplicate task id(s): " + ", ".join(quiz_dupes))

    return ParsedLesson(front_matter, meta, front_matter["topics"], blocks, practices, quizzes, warnings)


def parse_attrs(attr_str: str) -> dict:
    attrs = {}
    for m in re.finditer(r'(\w+)=("([^"]*)"|\'([^\']*)\'|(\S+))', attr_str):
        key = m.group(1)
        val = m.group(3) if m.group(3) is not None else (m.group(4) if m.group(4) is not None else m.group(5))
        attrs[key] = val
    return attrs


def split_fences(text: str):
    """Yield ('text', content) for plain runs and ('block', name, attrs, content)
    for ':::name ... :::' fences."""
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


def parse_blocks(text: str, practices: list, quizzes: list, warnings: list) -> list[Block]:
    """Split the body into ``## `` blocks. Content before the first ``## ``
    heading (if any) is folded into an unnumbered intro block so nothing
    written before the first heading is lost."""
    raw_blocks: list[tuple[str, str]] = []  # (title, raw_text)
    current_title = None
    current_lines: list[str] = []
    in_fence = False

    for line in text.split("\n"):
        if FENCE_RE.match(line.strip()):
            in_fence = not in_fence
            current_lines.append(line)
            continue
        m = BLOCK_HEADING_RE.match(line.strip()) if not in_fence else None
        if m:
            raw_blocks.append((current_title, "\n".join(current_lines)))
            current_title = m.group(1).strip()
            current_lines = []
        else:
            current_lines.append(line)
    raw_blocks.append((current_title, "\n".join(current_lines)))

    numbered = [(title, body) for title, body in raw_blocks if title is not None]
    intro = [(title, body) for title, body in raw_blocks if title is None and body.strip()]

    total = len(numbered)
    blocks: list[Block] = []
    for title, body in intro:
        nodes = parse_body(body, practices, quizzes, warnings)
        if nodes:
            blocks.append(Block(title="", index=0, total=total, nodes=nodes))
    for i, (title, body) in enumerate(numbered, start=1):
        nodes = parse_body(body, practices, quizzes, warnings)
        blocks.append(Block(title=title, index=i, total=total, nodes=nodes))

    if not numbered and not blocks:
        warnings.append("No `## ` block headings found — see skills/FORMAT_SPEC.md for the block format.")

    return blocks


def parse_body(text: str, practices: list, quizzes: list, warnings: list) -> list:
    nodes = []
    for kind, name, attrs, content in split_fences(text):
        if kind == "text":
            html_out = render_markdown(content)
            if html_out.strip():
                nodes.append(Prose(html_out))
        else:
            node = build_block(name, attrs, content, practices, quizzes, warnings)
            if node is not None:
                nodes.append(node)
    return nodes


def split_keyword_sections(text: str) -> dict:
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


def build_practice(attrs: dict, content: str, practices: list, warnings: list) -> Practice:
    practice_id = attrs.get("id")
    if not practice_id:
        practice_id = f"p{len(practices) + 1}"
        warnings.append(f"A :::practice block is missing id= — assigned a temporary id ({practice_id}).")

    hint_seconds = None
    hint_raw = attrs.get("hint")
    if hint_raw is not None:
        try:
            hint_seconds = int(hint_raw)
        except ValueError:
            warnings.append(f"Practice {practice_id}: hint= must be a whole number of seconds, got {hint_raw!r}.")

    sections = split_keyword_sections(content)
    question_html = render_markdown(sections.get(None, ""))

    expected = None
    if sections.get("EXPECTED", "").strip():
        expected = sections["EXPECTED"].strip()

    has_solution = bool(sections.get("SOLUTION", "").strip())
    solution_html = render_markdown(sections["SOLUTION"]) if has_solution else None

    practice = Practice(
        practice_id=practice_id, index=len(practices) + 1, hint_seconds=hint_seconds,
        question_html=question_html, expected=expected,
        solution_html=solution_html, has_solution=has_solution,
    )
    practices.append(practice)
    return practice


def render_inline(text: str) -> str:
    """Like render_markdown, but for a single line/phrase that shouldn't be
    wrapped in a <p> — an option label, a feedback message, a check line."""
    html_out = render_markdown(text)
    if html_out.startswith("<p>") and html_out.endswith("</p>"):
        html_out = html_out[3:-4]
    return html_out


DASH_SPLIT_RE = re.compile(r"\s+[—–]\s+|\s+--\s+|\s+-\s+")


def split_label_feedback(text: str) -> tuple[str, str]:
    """Split 'label — feedback' on the first em/en dash (or ` -- `/` - `
    fallback) into (label, feedback). feedback is "" if there's no dash."""
    m = DASH_SPLIT_RE.search(text)
    if not m:
        return text.strip(), ""
    return text[:m.start()].strip(), text[m.end():].strip()


def build_journey(content: str) -> Journey:
    """- time/emoji | title | detail | now(optional) -- one line per stage."""
    steps = []
    for raw in content.split("\n"):
        line = raw.strip()
        if not line.startswith("-"):
            continue
        parts = [p.strip() for p in line[1:].split("|")]
        steps.append({
            "time": parts[0] if len(parts) > 0 else "",
            "title": parts[1] if len(parts) > 1 else "",
            "detail": parts[2] if len(parts) > 2 else "",
            "current": len(parts) > 3 and parts[3].strip().lower() == "now",
        })
    return Journey(steps)


def build_figure(attrs: dict, content: str) -> Figure:
    return Figure(caption=attrs.get("caption", ""), art=content.strip("\n"))


OBJECTIVE_ITEM_RE = re.compile(r"^\d+\.\s+(.*)$")


def build_objectives(content: str) -> Objectives:
    """1. goal text / CHECK — success criteria (CHECK line optional)."""
    items: list[dict] = []
    current = None
    for raw in content.split("\n"):
        line = raw.strip()
        if not line:
            continue
        m = OBJECTIVE_ITEM_RE.match(line)
        if m:
            if current is not None:
                items.append(current)
            current = {"html": render_inline(m.group(1)), "check": ""}
        elif line.upper().startswith("CHECK") and current is not None:
            remainder = re.sub(r"^[—–-]+\s*", "", line[5:].strip())
            current["check"] = remainder
        elif current is not None:
            current["html"] += " " + render_inline(line)
    if current is not None:
        items.append(current)
    return Objectives(items)


def build_grid(content: str) -> Grid:
    """Two (or more) columns of plain lines, split by a lone `---` line.
    Each column's first line is its heading, the rest are items."""
    columns_raw: list[list[str]] = [[]]
    for raw in content.split("\n"):
        line = raw.strip()
        if line == "---":
            columns_raw.append([])
            continue
        if line:
            columns_raw[-1].append(line)
    columns = [{"heading": c[0], "items": c[1:]} for c in columns_raw if c]
    return Grid(columns)


def build_push(attrs: dict, content: str) -> Push:
    return Push(title=attrs.get("title", ""), html=render_markdown(content))


def build_checklist(content: str) -> Checklist:
    items = []
    for raw in content.split("\n"):
        line = raw.strip()
        if line.startswith("- "):
            items.append(line[2:].strip())
        elif line.startswith("-"):
            items.append(line[1:].strip())
    return Checklist(items)


def build_quiz(attrs: dict, content: str, quizzes: list, warnings: list):
    """Question text, then an OPTIONS line, then one `- label — feedback`
    per choice; prefix the correct one's label with [x]."""
    quiz_id = attrs.get("id")
    if not quiz_id:
        quiz_id = f"q{len(quizzes) + 1}"
        warnings.append(f"A :::task block is missing id= — assigned a temporary id ({quiz_id}).")

    question_lines: list[str] = []
    option_lines: list[str] = []
    seen_options = False
    for raw in content.split("\n"):
        if raw.strip().upper() == "OPTIONS":
            seen_options = True
            continue
        (option_lines if seen_options else question_lines).append(raw)

    options = []
    for raw in option_lines:
        line = raw.strip()
        if not line.startswith("-"):
            continue
        line = line[1:].strip()
        is_correct = False
        if line[:3] in ("[x]", "[X]"):
            is_correct = True
            line = line[3:].strip()
        elif line[:3] == "[ ]":
            line = line[3:].strip()
        label, feedback = split_label_feedback(line)
        options.append({
            "text_html": render_inline(label),
            "feedback_html": render_inline(feedback),
            "is_correct": is_correct,
        })

    if not options:
        warnings.append(f"Task {quiz_id}: no OPTIONS found — skipped.")
        return None
    if not any(o["is_correct"] for o in options):
        warnings.append(f"Task {quiz_id}: no option marked [x] as correct.")

    quiz = Quiz(quiz_id=quiz_id, question_html=render_markdown("\n".join(question_lines)), options=options)
    quizzes.append(quiz)
    return quiz


def build_block(name: str, attrs: dict, content: str, practices: list, quizzes: list, warnings: list):
    if name == "practice":
        return build_practice(attrs, content, practices, warnings)
    if name == "example":
        return Example(render_markdown(content))
    if name == "tip":
        return Tip(render_markdown(content))
    if name == "journey":
        return build_journey(content)
    if name == "figure":
        return build_figure(attrs, content)
    if name == "objectives":
        return build_objectives(content)
    if name == "grid":
        return build_grid(content)
    if name == "push":
        return build_push(attrs, content)
    if name == "checklist":
        return build_checklist(content)
    if name == "task" and attrs.get("type") == "choice":
        return build_quiz(attrs, content, quizzes, warnings)

    warnings.append(f"Unknown block type :::{name} — rendered as plain text so nothing is lost.")
    return Prose(render_markdown(content))

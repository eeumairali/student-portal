"""Parses the simplified lesson Markdown format described in
skills/FORMAT_SPEC.md into a tree of render-ready nodes. See
skills/LESSON_TEMPLATE.md for a worked example.

Nothing in this module touches the database — it is pure text in, node tree
out, so it can be reused for the admin preview and for the real save path.

The whole format is deliberately small: front matter, then a sequence of
``## `` blocks (auto-numbered "N of TOTAL"), each holding prose, an optional
``:::example`` panel, an optional ``:::tip`` note, and zero or more
``:::practice`` questions the student works out on their own computer. There
is no in-browser code execution, no blanks, no quizzes, no checklists.
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
    blocks = parse_blocks(body_text, practices, warnings)

    seen_ids: dict[str, int] = {}
    for p in practices:
        seen_ids[p.practice_id] = seen_ids.get(p.practice_id, 0) + 1
    dupes = [pid for pid, n in seen_ids.items() if n > 1]
    if dupes:
        warnings.append("Duplicate practice id(s), only the last will keep progress correctly: " + ", ".join(dupes))

    return ParsedLesson(front_matter, meta, front_matter["topics"], blocks, practices, warnings)


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


def parse_blocks(text: str, practices: list, warnings: list) -> list[Block]:
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
        nodes = parse_body(body, practices, warnings)
        if nodes:
            blocks.append(Block(title="", index=0, total=total, nodes=nodes))
    for i, (title, body) in enumerate(numbered, start=1):
        nodes = parse_body(body, practices, warnings)
        blocks.append(Block(title=title, index=i, total=total, nodes=nodes))

    if not numbered and not blocks:
        warnings.append("No `## ` block headings found — see skills/FORMAT_SPEC.md for the block format.")

    return blocks


def parse_body(text: str, practices: list, warnings: list) -> list:
    nodes = []
    for kind, name, attrs, content in split_fences(text):
        if kind == "text":
            html_out = render_markdown(content)
            if html_out.strip():
                nodes.append(Prose(html_out))
        else:
            node = build_block(name, attrs, content, practices, warnings)
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


def build_block(name: str, attrs: dict, content: str, practices: list, warnings: list):
    if name == "practice":
        return build_practice(attrs, content, practices, warnings)
    if name == "example":
        return Example(render_markdown(content))
    if name == "tip":
        return Tip(render_markdown(content))

    warnings.append(f"Unknown block type :::{name} — rendered as plain text so nothing is lost.")
    return Prose(render_markdown(content))

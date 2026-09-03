"""Parses a tutorial's Markdown front matter (domain, title, summary, ...).
Mirrors learning.lesson_markdown's front-matter handling, but far simpler —
tutorials have no practice questions or per-student data, just an article
body. Nothing here touches the database; see article_save.py for that."""
from __future__ import annotations

import re
from dataclasses import dataclass, field

import yaml

FRONT_MATTER_RE = re.compile(r"^---\s*\n(.*?\n)---[ \t]*\n?(.*)$", re.DOTALL)


@dataclass
class ParsedArticle:
    front_matter: dict
    body: str
    warnings: list = field(default_factory=list)


def parse_article(raw_text: str) -> ParsedArticle:
    warnings: list[str] = []
    raw_text = raw_text.lstrip("﻿")
    m = FRONT_MATTER_RE.match(raw_text)
    if not m:
        warnings.append(
            "No front matter found — the file must start with a `---` block naming domain: and title:."
        )
        return ParsedArticle({}, raw_text.strip("\n"), warnings)

    fm_raw, body = m.group(1), m.group(2)
    try:
        fm = yaml.safe_load(fm_raw) or {}
    except yaml.YAMLError as e:
        warnings.append(f"Front matter is not valid YAML: {e}")
        fm = {}
    if not isinstance(fm, dict):
        warnings.append("Front matter must be a mapping of key: value pairs.")
        fm = {}

    for required in ("domain", "title"):
        if not fm.get(required):
            warnings.append(f"Missing required field: {required}")

    return ParsedArticle(fm, body.strip("\n"), warnings)

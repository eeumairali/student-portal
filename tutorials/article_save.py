"""Turns a ParsedArticle (see article_editor.py) into a Tutorial row.

Two-step by design, matching learning.lesson_save: resolve_article_save_plan()
never writes anything — that's the preview step — save_article() only runs
once a tutor has confirmed."""
from __future__ import annotations

from dataclasses import dataclass, field

from django.utils.text import slugify

from .article_editor import ParsedArticle
from .models import Domain, Tutorial


class ArticleSaveError(Exception):
    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


@dataclass
class ArticleSavePlan:
    domain_name: str
    title: str
    existing: Tutorial | None
    warnings: list = field(default_factory=list)


def resolve_article_save_plan(parsed: ParsedArticle, *, target: Tutorial | None = None) -> ArticleSavePlan:
    """`target` is set when editing a specific existing article — the save
    always updates that exact row, so a title change doesn't fork off a
    second article instead of updating the one being edited."""
    warnings = list(parsed.warnings)

    domain_name = parsed.front_matter.get("domain")
    title = parsed.front_matter.get("title")
    if not domain_name or not title:
        raise ArticleSaveError("The document needs both domain: and title: in its front matter.")

    existing = target
    if existing is None:
        slug_hint = parsed.front_matter.get("slug")
        if slug_hint:
            existing = Tutorial.objects.filter(slug=slugify(str(slug_hint))).first()
        if existing is None:
            existing = Tutorial.objects.filter(title=title, domain__name__iexact=domain_name).first()
            if existing:
                warnings.append(
                    "An article with this domain and title already exists — it will be updated, not duplicated."
                )

    return ArticleSavePlan(domain_name=str(domain_name), title=str(title), existing=existing, warnings=warnings)


def save_article(parsed: ParsedArticle, plan: ArticleSavePlan) -> Tutorial:
    tutorial = plan.existing or Tutorial()
    tutorial.domain = Domain.get_or_create_by_name(plan.domain_name)
    tutorial.title = plan.title

    slug_hint = parsed.front_matter.get("slug")
    if not tutorial.pk or slug_hint:
        base_slug = slugify(str(slug_hint)) if slug_hint else slugify(plan.title)
        slug = base_slug
        i = 2
        while Tutorial.objects.filter(slug=slug).exclude(pk=tutorial.pk).exists():
            slug = f"{base_slug}-{i}"
            i += 1
        tutorial.slug = slug

    tutorial.summary = str(parsed.front_matter.get("summary") or "")
    tutorial.body = parsed.body
    tutorial.is_published = bool(parsed.front_matter.get("visible", True))

    order = parsed.front_matter.get("order")
    try:
        if order is not None:
            tutorial.order = int(order)
        elif not tutorial.pk:
            tutorial.order = 1
    except (TypeError, ValueError):
        pass

    tutorial.save()
    return tutorial

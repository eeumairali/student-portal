from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from .article_editor import parse_article
from .article_save import ArticleSaveError, resolve_article_save_plan, save_article
from .models import Domain, Tutorial, render_markdown

SAMPLE_ARTICLE = """---
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
"""


# ------------------------------------------------------------------- public --

def home(request):
    domains = [d for d in Domain.objects.all() if d.published_tutorial_count() > 0]
    return render(request, "tutorials/home.html", {"domains": domains})


def domain_detail(request, slug):
    domain = get_object_or_404(Domain, slug=slug)
    tutorials = domain.tutorials.filter(is_published=True)
    return render(request, "tutorials/domain_detail.html", {"domain": domain, "tutorials": tutorials})


def tutorial_detail(request, slug):
    tutorial = get_object_or_404(Tutorial, slug=slug, is_published=True)
    return render(request, "tutorials/tutorial_detail.html", {"tutorial": tutorial})


# --------------------------------------------------------------- staff tool --

@staff_member_required
def article_list(request):
    """Every public article, tutor-only. Mirrors learning.student_list —
    the roster for the other kind of content this site publishes."""
    tutorials = Tutorial.objects.select_related("domain").order_by("domain__name", "order", "title")
    return render(request, "tutorials/tutor/article_list.html", {"tutorials": tutorials})


def _markdown_for_editing(tutorial: Tutorial) -> str:
    visible = "true" if tutorial.is_published else "false"
    return (
        f"---\ndomain: {tutorial.domain.name}\ntitle: {tutorial.title}\n"
        f"summary: {tutorial.summary}\norder: {tutorial.order}\nvisible: {visible}\n"
        f"---\n\n{tutorial.body}"
    )


@staff_member_required
def article_upload(request, tutorial_id=None):
    """Paste or upload a Markdown article — also doubles as the editor for an
    existing one when tutorial_id is given. Two-step: always previews first;
    nothing saves until 'Confirm & publish' posts back here with action=confirm.
    Mirrors learning.views.lesson_upload."""
    editing = None
    if tutorial_id is not None:
        editing = get_object_or_404(Tutorial, pk=tutorial_id)

    editor_url = (
        reverse("article_edit", args=[editing.id]) if editing else reverse("article_upload")
    )

    if request.method != "POST":
        markdown = _markdown_for_editing(editing) if editing else SAMPLE_ARTICLE
        return render(request, "tutorials/tutor/article_upload.html", {
            "markdown": markdown, "editing": editing,
        })

    raw = request.POST.get("markdown", "")
    upload = request.FILES.get("file")
    if upload:
        raw = upload.read().decode("utf-8", errors="replace")

    parsed = parse_article(raw)
    try:
        plan = resolve_article_save_plan(parsed, target=editing)
        error = None
    except ArticleSaveError as e:
        plan = None
        error = e.message

    if request.POST.get("action") == "confirm" and plan is not None:
        save_article(parsed, plan)
        return redirect("article_list")

    return render(request, "tutorials/tutor/article_preview.html", {
        "front_matter": parsed.front_matter,
        "body_html": render_markdown(parsed.body),
        "markdown": raw, "plan": plan, "error": error,
        "editing": editing, "back_to_editor_url": editor_url,
    })


@staff_member_required
@require_POST
def article_delete(request, tutorial_id):
    tutorial = get_object_or_404(Tutorial, pk=tutorial_id)
    tutorial.delete()
    return redirect("article_list")

from django.db import models
from django.utils.text import slugify

import markdown as md

MD_EXTENSIONS = ["tables", "fenced_code", "sane_lists", "codehilite"]
MD_EXTENSION_CONFIGS = {
    "codehilite": {"css_class": "hl", "guess_lang": False},
}


def render_markdown(text: str) -> str:
    text = (text or "").strip("\n")
    if not text.strip():
        return ""
    return md.markdown(text, extensions=MD_EXTENSIONS, extension_configs=MD_EXTENSION_CONFIGS)


class Domain(models.Model):
    """A public tutorial category, e.g. 'Python' or 'Webots'. Created on the
    fly (see tutorials.admin) whenever a tutor types a new domain name while
    adding a Tutorial — no code change needed to add a new domain."""

    name = models.CharField(max_length=80, unique=True)
    slug = models.SlugField(max_length=100, unique=True, blank=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    @classmethod
    def get_or_create_by_name(cls, name: str) -> "Domain":
        name = name.strip()
        existing = cls.objects.filter(name__iexact=name).first()
        if existing:
            return existing
        return cls.objects.create(name=name, slug=slugify(name))

    def published_tutorial_count(self):
        return self.tutorials.filter(is_published=True).count()


class Tutorial(models.Model):
    """A public article/tutorial, browsable by anyone without logging in.
    Kept separate from learning.Lesson — this is marketing/SEO content, not
    the paid one-to-one tutoring material."""

    domain = models.ForeignKey(Domain, on_delete=models.CASCADE, related_name="tutorials")
    title = models.CharField(max_length=140)
    slug = models.SlugField(max_length=160, unique=True)
    summary = models.CharField(
        max_length=300, blank=True,
        help_text="Short blurb shown on cards and used as the page's meta description.",
    )
    body = models.TextField(blank=True, help_text="Article content, written in Markdown.")
    order = models.PositiveIntegerField(default=1, help_text="Position within its domain.")
    is_published = models.BooleanField(default=True, help_text="Untick to hide from the public site.")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["domain__name", "order", "title"]

    def __str__(self):
        return self.title

    @property
    def body_html(self):
        return render_markdown(self.body)

from django import forms
from django.contrib import admin

from .models import Domain, Tutorial


class TutorialAdminForm(forms.ModelForm):
    """Replaces the domain FK dropdown with a free-text field: type any
    domain name (new or existing) and it's resolved/created on save."""

    domain_name = forms.CharField(
        max_length=80, label="Domain",
        help_text="e.g. 'Python' or 'Webots'. A new name creates a new domain automatically.",
    )

    class Meta:
        model = Tutorial
        exclude = ["domain"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk and self.instance.domain_id:
            self.fields["domain_name"].initial = self.instance.domain.name

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.domain = Domain.get_or_create_by_name(self.cleaned_data["domain_name"])
        if commit:
            instance.save()
        return instance


@admin.register(Domain)
class DomainAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "tutorial_count", "created_at")
    search_fields = ("name",)
    prepopulated_fields = {"slug": ("name",)}

    @admin.display(description="Tutorials")
    def tutorial_count(self, obj):
        return obj.tutorials.count()


@admin.register(Tutorial)
class TutorialAdmin(admin.ModelAdmin):
    form = TutorialAdminForm
    list_display = ("title", "domain", "order", "is_published", "updated_at")
    list_filter = ("domain", "is_published")
    search_fields = ("title", "summary", "body")
    prepopulated_fields = {"slug": ("title",)}
    fieldsets = (
        (None, {"fields": ("domain_name", "title", "slug", "order", "is_published")}),
        ("Content", {"fields": ("summary", "body")}),
    )

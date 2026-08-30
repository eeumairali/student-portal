from django.conf import settings
from django.db import models


class StudentProfile(models.Model):
    """Tutor-facing detail about a learner. Kept deliberately small: only fields
    needed to run lessons and reach a guardian. No date of birth, no address."""

    PLATFORMS = [
        ("fiverr", "Fiverr"),
        ("preply", "Preply"),
        ("direct", "Direct / Zoom"),
    ]

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="student_profile"
    )
    display_name = models.CharField(
        max_length=60, help_text="What the student is called in lessons. A first name is enough."
    )
    platform = models.CharField(max_length=20, choices=PLATFORMS, default="direct")
    is_minor = models.BooleanField(
        default=False, help_text="Tick if under 18. Guardian contact is then required."
    )
    guardian_email = models.EmailField(
        blank=True, help_text="Only for students under 18. Leave empty otherwise."
    )
    notes = models.TextField(
        blank=True, help_text="Teaching notes only. Do not store anything sensitive here."
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["display_name"]

    def __str__(self):
        return self.display_name

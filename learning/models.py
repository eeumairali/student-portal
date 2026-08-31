import uuid
from pathlib import Path

from django.conf import settings
from django.db import models
from django.utils import timezone


def lesson_file_path(instance, filename):
    """Unguessable storage path. The original filename is kept in a field,
    not in the path, so nobody can enumerate uploads."""
    suffix = Path(filename).suffix.lower()
    return f"lessons/{uuid.uuid4().hex}{suffix}"


class Course(models.Model):
    SUBJECTS = [
        ("python", "Python"),
        ("data", "Data science"),
        ("ml", "Machine learning / computer vision"),
        ("matlab", "MATLAB"),
        ("robotics", "Arduino / Webots robotics"),
        ("exam", "Exam preparation"),
    ]

    title = models.CharField(max_length=120)
    slug = models.SlugField(unique=True)
    subject = models.CharField(max_length=20, choices=SUBJECTS, default="python")
    description = models.TextField(blank=True)
    is_published = models.BooleanField(
        default=True, help_text="Untick to hide from students while you build it."
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["title"]

    def __str__(self):
        return self.title

    def visible_lessons(self):
        """Unpublished-filtered only — NOT student-scoped. A course's personal
        (student-owned) lessons must never be shown to another student, so
        anything student-facing should go through services.course_progress,
        not this. Safe for staff/admin-wide use only."""
        return self.lessons.filter(is_published=True)


class Enrollment(models.Model):
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="enrollments"
    )
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="enrollments")
    started_on = models.DateField(default=timezone.localdate)
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = [("student", "course")]
        ordering = ["-started_on"]

    def __str__(self):
        return f"{self.student} → {self.course}"


class Lesson(models.Model):
    # Shared curriculum lesson (Phase 1): course set, student blank, ordered by `order`.
    # Personal dated document (Phase 2): student + date set, markdown_source holds the
    # document. course is then just an optional grouping label. Never delete a Lesson —
    # `is_published` ("visible" in the front matter) is how a tutor locks/unlocks it.
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="lessons", null=True, blank=True)
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="personal_lessons",
        null=True, blank=True, help_text="Set for a dated document written for one student.",
    )
    date = models.DateField(null=True, blank=True, help_text="Orders this on the student's timeline.")
    order = models.PositiveIntegerField(default=1, help_text="Position in the course (shared curriculum lessons only).")
    title = models.CharField(max_length=140)
    subtitle = models.CharField(max_length=255, blank=True)
    description = models.TextField(blank=True, help_text="What the student will do this session. (Legacy field — new lessons use markdown_source.)")
    markdown_source = models.TextField(blank=True, help_text="The lesson document. See skills/FORMAT_SPEC.md.")
    meta = models.JSONField(default=dict, blank=True, help_text="Unknown front-matter keys, rendered as header pills.")
    hint_seconds_default = models.PositiveIntegerField(default=20)
    is_published = models.BooleanField(default=True, help_text="Locked (unticked) lessons are invisible to the student.")

    class Meta:
        ordering = ["-date", "order", "id"]

    def __str__(self):
        return self.title

    @property
    def is_document(self):
        return bool(self.markdown_source)


class LessonFile(models.Model):
    KINDS = [
        ("slides", "Slides"),
        ("notebook", "Notebook"),
        ("dataset", "Dataset"),
        ("handout", "Handout"),
        ("other", "Other"),
    ]

    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name="files")
    label = models.CharField(max_length=120, help_text="What the student sees, e.g. 'Session 3 slides'.")
    kind = models.CharField(max_length=20, choices=KINDS, default="other")
    upload = models.FileField(upload_to=lesson_file_path)
    original_name = models.CharField(max_length=255, blank=True, editable=False)
    size_bytes = models.PositiveBigIntegerField(default=0, editable=False)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["kind", "label"]

    def save(self, *args, **kwargs):
        if self.upload and not self.original_name:
            self.original_name = Path(self.upload.name).name
        if self.upload:
            try:
                self.size_bytes = self.upload.size
            except (OSError, ValueError):
                pass
        super().save(*args, **kwargs)

    def __str__(self):
        return self.label

    @property
    def pretty_size(self):
        size = float(self.size_bytes)
        for unit in ("B", "KB", "MB", "GB"):
            if size < 1024 or unit == "GB":
                return f"{size:.0f} {unit}" if unit == "B" else f"{size:.1f} {unit}"
            size /= 1024


class Task(models.Model):
    """One row per :::practice question in a lesson's markdown_source. This is
    identity and state only — content is re-parsed live from markdown_source
    on every view, so it can never drift from what's on the page. A practice
    removed from the source is marked orphaned, never deleted, so a student's
    progress on it is never silently lost."""

    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name="tasks")
    task_id = models.CharField(max_length=64)
    order = models.PositiveIntegerField(default=1)
    is_orphaned = models.BooleanField(default=False, help_text="No longer in the markdown source.")
    is_complete = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = [("lesson", "task_id")]
        ordering = ["order"]

    def __str__(self):
        return f"{self.lesson} · {self.task_id}"

    def mark(self, complete):
        self.is_complete = complete
        self.completed_at = timezone.now() if complete else None
        self.save(update_fields=["is_complete", "completed_at"])


class HintReveal(models.Model):
    """Append-only log — every time a student presses 'I'm stuck' and the
    timer runs out. The most useful signal for the tutor view: it shows
    where a student actually struggled, which a completion tick does not."""

    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name="hint_reveals")
    task_id = models.CharField(max_length=64)
    revealed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["revealed_at"]

    def __str__(self):
        return f"{self.lesson} · {self.task_id} · {self.revealed_at:%Y-%m-%d %H:%M}"


class LessonProgress(models.Model):
    """One row per student per lesson, created the first time they tick it."""

    student = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="lesson_progress"
    )
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name="progress")
    is_complete = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = [("student", "lesson")]
        verbose_name_plural = "Lesson progress"

    def mark(self, complete):
        self.is_complete = complete
        self.completed_at = timezone.now() if complete else None
        self.save(update_fields=["is_complete", "completed_at", "updated_at"])

    def __str__(self):
        return f"{self.student} · {self.lesson} · {'done' if self.is_complete else 'open'}"

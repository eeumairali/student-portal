"""Turns a ParsedLesson (see lesson_markdown.py) into database rows.

Two-step by design: resolve_save_plan() never writes anything — it's the
preview step, and it's where a bad upload gets caught (unknown student,
misfiled document). save_lesson() only runs once a tutor has confirmed.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from django.contrib.auth.models import User
from django.utils.text import slugify

from .lesson_markdown import ParsedLesson
from .models import Course, Enrollment, HintReveal, Lesson, Task


class LessonSaveError(Exception):
    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


@dataclass
class SavePlan:
    student: User
    course: Course | None
    existing_lesson: Lesson | None
    removed_tasks: list = field(default_factory=list)  # [(task_id, has_progress), ...]
    warnings: list = field(default_factory=list)


def resolve_save_plan(
    parsed: ParsedLesson, *, locked_student: User | None = None, target_lesson: Lesson | None = None
) -> SavePlan:
    """Validate and figure out what save_lesson() would do, without touching
    the database. `locked_student` is the student whose page the tutor is
    uploading from — if the front matter names someone else, this is a
    misfile and gets rejected rather than silently overridden or ignored.

    `target_lesson` is set when the tutor is editing a specific existing
    lesson (see lesson_edit): the save always updates that exact row, even
    if the title or date changed — matching by (student, date, title) alone
    would otherwise treat a rename as a brand new lesson and silently
    orphan the one being edited."""
    warnings = list(parsed.warnings)

    username = parsed.front_matter.get("student")
    if not username:
        raise LessonSaveError("The document has no student: field — see skills/FORMAT_SPEC.md.")

    student = User.objects.filter(username=username).first()
    if student is None:
        raise LessonSaveError(f"No student with username '{username}'. Students are never created automatically.")

    if locked_student is not None and student.pk != locked_student.pk:
        raise LessonSaveError(
            f"This document's front matter says student: {username}, but you're uploading it on "
            f"{locked_student.username}'s page. Fix the file, or upload it from {username}'s page instead."
        )

    if target_lesson is not None and target_lesson.student_id != student.pk:
        raise LessonSaveError(
            f"This document's front matter says student: {username}, but you're editing a lesson that "
            f"belongs to {target_lesson.student.username}. The student on an existing lesson can't be changed here."
        )

    course = None
    course_key = parsed.front_matter.get("course")
    if course_key:
        course, _ = Course.objects.get_or_create(
            slug=slugify(course_key),
            defaults={"title": str(course_key).replace("-", " ").replace("_", " ").title()},
        )

    date = parsed.front_matter.get("date")
    title = parsed.front_matter.get("title")
    existing_lesson = target_lesson
    if existing_lesson is None and date and title:
        existing_lesson = Lesson.objects.filter(student=student, date=date, title=title).first()
        if existing_lesson:
            warnings.append("A lesson with this student, date and title already exists — it will be updated, not duplicated.")

    removed_tasks: list = []
    if existing_lesson:
        new_ids = {p.practice_id for p in parsed.practices}
        for task in existing_lesson.tasks.filter(is_orphaned=False):
            if task.task_id not in new_ids:
                has_progress = task.is_complete or HintReveal.objects.filter(
                    lesson=existing_lesson, task_id=task.task_id
                ).exists()
                removed_tasks.append((task.task_id, has_progress))

    return SavePlan(student=student, course=course, existing_lesson=existing_lesson,
                     removed_tasks=removed_tasks, warnings=warnings)


def save_lesson(parsed: ParsedLesson, raw_markdown: str, plan: SavePlan) -> Lesson:
    lesson = plan.existing_lesson or Lesson()
    lesson.student = plan.student
    lesson.course = plan.course
    lesson.date = parsed.front_matter.get("date")
    lesson.title = parsed.front_matter.get("title", "")
    lesson.subtitle = parsed.front_matter.get("subtitle") or ""
    lesson.markdown_source = raw_markdown
    lesson.meta = parsed.meta
    hint_default = parsed.front_matter.get("hint_seconds")
    try:
        lesson.hint_seconds_default = int(hint_default) if hint_default else 20
    except (TypeError, ValueError):
        lesson.hint_seconds_default = 20
    lesson.is_published = bool(parsed.front_matter.get("visible", False))
    lesson.description = ""
    lesson.save()

    new_ids = {p.practice_id for p in parsed.practices}
    for order, p in enumerate(parsed.practices, start=1):
        Task.objects.update_or_create(
            lesson=lesson, task_id=p.practice_id,
            defaults={"order": order, "is_orphaned": False},
        )
    Task.objects.filter(lesson=lesson).exclude(task_id__in=new_ids).update(is_orphaned=True)

    if lesson.course_id:
        # A session filed under a course is what "doing that course" means
        # here — the student should see it on their dashboard without a
        # tutor having to separately remember to enrol them.
        enrollment, created = Enrollment.objects.get_or_create(
            student=lesson.student, course=lesson.course, defaults={"is_active": True}
        )
        if not created and not enrollment.is_active:
            enrollment.is_active = True
            enrollment.save(update_fields=["is_active"])

    return lesson

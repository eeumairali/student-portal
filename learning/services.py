"""Shared query helpers. Everything a student can reach is filtered by
enrolment (or, for a personal dated lesson, by student match) here, so no
view can accidentally leak another student's data."""
from django.db.models import Q
from django.http import Http404
from django.shortcuts import get_object_or_404

from .models import Course, Enrollment, Lesson, LessonProgress, Task


def enrolled_courses(user):
    return Course.objects.filter(
        enrollments__student=user, enrollments__is_active=True, is_published=True
    ).distinct()


def get_enrolled_course(user, slug):
    return get_object_or_404(enrolled_courses(user), slug=slug)


def get_accessible_lesson(user, lesson_id):
    """A personal dated lesson (student set) is reachable only by that
    student or by staff. A shared curriculum lesson (student blank) needs
    an active enrolment in its course, as before. A locked (unpublished)
    lesson is invisible to the student either way — that's the tutor's
    lock/unlock control."""
    lesson = get_object_or_404(Lesson.objects.select_related("course"), pk=lesson_id)
    if lesson.student_id is not None:
        if lesson.student_id == user.id or user.is_staff:
            if lesson.is_published or user.is_staff:
                return lesson
        raise Http404
    if (
        lesson.is_published
        and lesson.course
        and lesson.course.is_published
        and Enrollment.objects.filter(student=user, course=lesson.course, is_active=True).exists()
    ):
        return lesson
    raise Http404


def student_lessons(student, *, include_locked=False):
    qs = Lesson.objects.filter(student=student).order_by("-date", "-id")
    if not include_locked:
        qs = qs.filter(is_published=True)
    return qs


def course_progress(user, course):
    """A course's session notes are personal — a lesson with `student` set
    must be this user's own, never another student's under the same course.
    Shared curriculum lessons (student blank) are visible to every enrolled
    student, as before."""
    lessons = list(
        course.lessons.filter(is_published=True)
        .filter(Q(student__isnull=True) | Q(student=user))
        .order_by("-date", "order", "id")
    )
    shared_lessons = [l for l in lessons if not l.is_document]
    document_lessons = [l for l in lessons if l.is_document]

    done_ids = set(
        LessonProgress.objects.filter(
            student=user, lesson__in=shared_lessons, is_complete=True
        ).values_list("lesson_id", flat=True)
    )
    if document_lessons:
        tasks_by_lesson = {}
        for task in Task.objects.filter(lesson__in=document_lessons, is_orphaned=False):
            tasks_by_lesson.setdefault(task.lesson_id, []).append(task)
        for lesson in document_lessons:
            tasks = tasks_by_lesson.get(lesson.id, [])
            if tasks and all(t.is_complete for t in tasks):
                done_ids.add(lesson.id)

    total = len(lessons)
    done = len(done_ids)
    return {
        "lessons": lessons,
        "shared_lessons": shared_lessons,
        "document_lessons": document_lessons,
        "done_ids": done_ids,
        "total": total,
        "done": done,
        "percent": round(done / total * 100) if total else 0,
    }


def is_enrolled(user, course):
    return Enrollment.objects.filter(student=user, course=course, is_active=True).exists()

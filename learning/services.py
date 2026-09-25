"""Shared query helpers. Everything a student can reach is filtered by
enrolment (or, for a personal dated lesson, by student match) here, so no
view can accidentally leak another student's data."""
from datetime import timedelta

from django.db.models import Q
from django.http import Http404
from django.shortcuts import get_object_or_404

from .lesson_markdown import Practice, Quiz, TaskBlock, parse_lesson
from .models import Course, Enrollment, HintReveal, Lesson, LessonProgress, QuizAttempt, Task


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


def leaderboard_rows(min_attempts=3):
    """One row per active student who has answered at least `min_attempts`
    graded quiz questions (across all their personal lessons), ranked for
    both the "most correct" and "highest accuracy" boards. The minimum
    keeps a single lucky guess from topping the accuracy board."""
    from accounts.models import StudentProfile

    rows = []
    profiles = StudentProfile.objects.filter(is_archived=False).select_related("user")
    for profile in profiles:
        attempts = QuizAttempt.objects.filter(lesson__student=profile.user)
        best_by_question = {}
        for attempt in attempts.order_by("lesson_id", "quiz_id", "-is_correct", "-answered_at"):
            best_by_question.setdefault((attempt.lesson_id, attempt.quiz_id), attempt.is_correct)
        total = len(best_by_question)
        if total < min_attempts:
            continue
        correct = sum(best_by_question.values())
        rows.append({
            "student": profile.user,
            "display_name": profile.display_name,
            "correct": correct,
            "total": total,
            "percent": round(correct / total * 100),
        })
    return rows


SECOND_CHANCE_SECONDS = 60


def wrong_quiz_attempts(lesson, parsed=None):
    """{quiz_id: latest attempt} for every choice question in the lesson whose
    most recent answer is wrong. A question answered correctly later (on the
    lesson page or on a second chance) drops out."""
    parsed = parsed or parse_lesson(lesson.markdown_source or "")
    current_ids = {quiz.quiz_id for quiz in parsed.quizzes}
    latest = {}
    for attempt in QuizAttempt.objects.filter(lesson=lesson, quiz_id__in=current_ids).order_by("answered_at", "id"):
        latest[attempt.quiz_id] = attempt
    return {quiz_id: attempt for quiz_id, attempt in latest.items() if not attempt.is_correct}


def second_chance_rows(student, *, include_locked=False):
    """One row per notebook where the student still has wrong answers: how
    many, and when the redo opens (SECOND_CHANCE_SECONDS after the most
    recent wrong answer in that notebook)."""
    lessons = student_lessons(student, include_locked=include_locked).exclude(markdown_source="")
    rows = []
    for lesson in lessons.filter(quiz_attempts__is_correct=False).distinct():
        parsed = parse_lesson(lesson.markdown_source)
        wrong = wrong_quiz_attempts(lesson, parsed)
        if not wrong:
            continue
        last_wrong_at = max(attempt.answered_at for attempt in wrong.values())
        rows.append({
            "lesson": lesson,
            "wrong_count": len(wrong),
            "quiz_total": len(parsed.quizzes),
            "available_at": last_wrong_at + timedelta(seconds=SECOND_CHANCE_SECONDS),
        })
    return rows


def second_chance_sections(parsed, wrong_ids):
    """The wrong questions grouped under the lesson section they came from,
    with that section's teaching content (prose, examples, tips…) so the
    student can re-read it before trying again. Other questions and
    practice steps in the section are left out."""
    skip = (Quiz, Practice, TaskBlock)
    sections = []
    for block in parsed.blocks:
        quizzes = [n for n in block.nodes if isinstance(n, Quiz) and n.quiz_id in wrong_ids]
        if quizzes:
            sections.append({
                "block": block,
                "content": [n for n in block.nodes if not isinstance(n, skip)],
                "quizzes": quizzes,
            })
    return sections


def student_progress_report(student):
    """Build a current, parent-friendly report from saved lesson activity."""
    lessons = list(Lesson.objects.filter(student=student).order_by("date", "id"))
    sessions = []
    topic_names = []
    total_tasks = completed_tasks = total_quizzes = correct_quizzes = hints = 0

    for lesson in lessons:
        parsed = parse_lesson(lesson.markdown_source or "")
        tasks = list(Task.objects.filter(lesson=lesson, is_orphaned=False))
        attempts = list(QuizAttempt.objects.filter(lesson=lesson))
        practice_count = len(parsed.practices)
        question_count = practice_count + len(parsed.quizzes)
        completed = sum(1 for task in tasks if task.is_complete)
        correct = sum(1 for attempt in attempts if attempt.is_correct)
        lesson_hints = HintReveal.objects.filter(lesson=lesson).count()
        topics = [str(topic) for topic in parsed.topics if str(topic).strip()] or [lesson.title]

        topic_names.extend(topics)
        total_tasks += len(tasks)
        completed_tasks += completed
        total_quizzes += len(attempts)
        correct_quizzes += correct
        hints += lesson_hints
        sessions.append({
            "lesson": lesson, "topics": topics, "question_count": question_count,
            "practice_count": practice_count, "quiz_count": len(parsed.quizzes),
            "completed_tasks": completed, "task_count": len(tasks),
            "quiz_answered": len(attempts), "quiz_correct": correct,
            "hints": lesson_hints, "complete": bool(tasks) and completed == len(tasks),
        })

    task_percent = round(completed_tasks / total_tasks * 100) if total_tasks else 0
    quiz_percent = round(correct_quizzes / total_quizzes * 100) if total_quizzes else 0
    if not lessons:
        strengths = ["The first learning session has not been recorded yet."]
        next_steps = ["Begin with a lesson so progress can be measured over time."]
    else:
        strengths = []
        if task_percent >= 80:
            strengths.append("Consistently works through practical questions and activities.")
        if total_quizzes and quiz_percent >= 70:
            strengths.append("Shows a good understanding in checked questions.")
        if hints == 0 and total_tasks:
            strengths.append("Works independently without needing recorded hints.")
        if not strengths:
            strengths.append("Is building a useful learning record through regular practice.")

        next_steps = []
        if total_tasks and task_percent < 100:
            next_steps.append("Finish the remaining practice activities and revisit any unfinished steps.")
        if total_quizzes and quiz_percent < 70:
            next_steps.append("Review the topics behind the questions answered incorrectly, then try similar examples.")
        if hints:
            next_steps.append("Practise the areas where hints were needed, aiming to solve the next example independently.")
        if not next_steps:
            next_steps.append("Continue with progressively more challenging problems and explain the reasoning aloud.")

    return {
        "student": student, "sessions": sessions,
        "topics": list(dict.fromkeys(topic_names)), "lesson_count": len(lessons),
        "completed_tasks": completed_tasks, "total_tasks": total_tasks, "task_percent": task_percent,
        "correct_quizzes": correct_quizzes, "total_quizzes": total_quizzes, "quiz_percent": quiz_percent,
        "hint_count": hints, "strengths": strengths, "next_steps": next_steps,
    }

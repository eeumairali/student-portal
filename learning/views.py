import json
import mimetypes

from django.conf import settings
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import FileResponse, Http404, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from accounts.models import StudentProfile

from .lesson_markdown import FORMATS, group_into_sections, parse_lesson
from .lesson_save import LessonSaveError, resolve_save_plan, save_lesson
from .models import BlankAnswer, ChecklistCheck, Course, HintReveal, Lesson, LessonFile, LessonProgress, Task
from .services import (
    course_progress, enrolled_courses, get_accessible_lesson, get_enrolled_course, student_lessons,
)

SAMPLE_LESSON_PATH = settings.BASE_DIR / "skills" / "LESSON_TEMPLATE.md"


def _document_context(parsed, *, lesson=None, can_edit=False, preview_warnings=None, preview_markdown=None,
                       back_to_editor_url=None):
    """Shared context builder for anything that renders learning/lesson/document.html
    or its _document_body.html partial: the staff preview tool, a student's own
    lesson page, and the tutor's read-only view of a student's lesson."""
    for i, task in enumerate(parsed.tasks, start=1):
        task.index = i
        task.effective_hint_seconds = (
            task.hint_seconds if task.hint_seconds is not None else parsed.hint_seconds_default
        )

    fmt = parsed.format if parsed.format in FORMATS else "document"

    initial_state = {"answers": {}, "completed": [], "checked": []}
    if lesson is not None and lesson.pk:
        initial_state["answers"] = dict(
            BlankAnswer.objects.filter(lesson=lesson).values_list("blank_id", "value")
        )
        initial_state["completed"] = list(
            Task.objects.filter(lesson=lesson, is_complete=True).values_list("task_id", flat=True)
        )
        initial_state["checked"] = list(
            ChecklistCheck.objects.filter(lesson=lesson, is_checked=True).values_list("check_id", flat=True)
        )

    return {
        "front_matter": parsed.front_matter,
        "meta_pills": [(k.replace("_", " ").capitalize(), v) for k, v in parsed.meta.items()],
        "course": parsed.front_matter.get("course"),
        "nodes": parsed.nodes,
        "sections": group_into_sections(parsed.nodes),
        "tasks": parsed.tasks,
        "format": fmt,
        "lesson_id": lesson.id if (lesson is not None and lesson.pk) else "",
        "can_edit": can_edit,
        "initial_state_json": json.dumps(initial_state),
        "preview_warnings": preview_warnings,
        "preview_markdown": preview_markdown,
        "back_to_editor_url": back_to_editor_url,
    }


@login_required
def dashboard(request):
    courses = enrolled_courses(request.user)
    cards = [{"course": c, **course_progress(request.user, c)} for c in courses]
    notes = student_lessons(request.user)
    return render(request, "learning/dashboard.html", {"cards": cards, "notes": notes})


@login_required
def course_detail(request, slug):
    course = get_enrolled_course(request.user, slug)
    progress = course_progress(request.user, course)
    return render(request, "learning/course_detail.html", {"course": course, **progress})


@login_required
def lesson_detail(request, lesson_id):
    lesson = get_accessible_lesson(request.user, lesson_id)

    if lesson.is_document:
        parsed = parse_lesson(lesson.markdown_source)
        context = _document_context(parsed, lesson=lesson, can_edit=(request.user.id == lesson.student_id))
        context["locked"] = not lesson.is_published
        return render(request, "learning/lesson_document_detail.html", context)

    record = LessonProgress.objects.filter(student=request.user, lesson=lesson).first()
    return render(
        request,
        "learning/lesson_detail.html",
        {
            "lesson": lesson,
            "course": lesson.course,
            "files": lesson.files.all(),
            "is_complete": bool(record and record.is_complete),
            **course_progress(request.user, lesson.course),
        },
    )


@login_required
@require_POST
def toggle_lesson(request, lesson_id):
    lesson = get_accessible_lesson(request.user, lesson_id)
    record, _ = LessonProgress.objects.get_or_create(student=request.user, lesson=lesson)
    record.mark(not record.is_complete)

    if request.headers.get("HX-Request"):
        return render(
            request,
            "learning/_lesson_status.html",
            {
                "lesson": lesson,
                "course": lesson.course,
                "is_complete": record.is_complete,
                **course_progress(request.user, lesson.course),
            },
        )
    return redirect("lesson_detail", lesson_id=lesson.id)


@login_required
def lesson_file(request, file_id):
    """The only route to a lesson file. Files sit outside the web root, so an
    unauthenticated URL guess cannot reach them even if the id leaks."""
    lesson_file = get_object_or_404(LessonFile.objects.select_related("lesson__course"), pk=file_id)
    get_accessible_lesson(request.user, lesson_file.lesson_id)

    try:
        handle = lesson_file.upload.open("rb")
    except FileNotFoundError:
        raise Http404("That file is missing. Ask your tutor to re-upload it.")

    filename = lesson_file.original_name or "download"
    content_type = mimetypes.guess_type(filename)[0] or "application/octet-stream"
    response = FileResponse(handle, as_attachment=True, filename=filename)
    response["Content-Type"] = content_type
    response["Cache-Control"] = "private, no-store"
    return response


# ---------------------------------------------------------- saving progress --

def _owned_lesson_or_404(request, lesson_id):
    """A student may only write their own answers/progress — never a tutor's
    guess and never another student's, even if they can view a lesson."""
    lesson = get_object_or_404(Lesson, pk=lesson_id, student=request.user)
    if not lesson.is_published:
        raise Http404
    return lesson


@login_required
@require_POST
def lesson_save_answer(request, lesson_id):
    lesson = _owned_lesson_or_404(request, lesson_id)
    data = json.loads(request.body or "{}")
    blank_id = (data.get("blank_id") or "")[:64]
    if not blank_id:
        return JsonResponse({"ok": False}, status=400)
    BlankAnswer.objects.update_or_create(
        lesson=lesson, blank_id=blank_id, defaults={"value": data.get("value", "")}
    )
    return JsonResponse({"ok": True})


@login_required
@require_POST
def lesson_toggle_task(request, lesson_id, task_id):
    lesson = _owned_lesson_or_404(request, lesson_id)
    data = json.loads(request.body or "{}")
    task, _ = Task.objects.get_or_create(lesson=lesson, task_id=task_id)
    task.mark(bool(data.get("complete")))
    return JsonResponse({"ok": True})


@login_required
@require_POST
def lesson_reveal_hint(request, lesson_id, task_id):
    lesson = _owned_lesson_or_404(request, lesson_id)
    HintReveal.objects.create(lesson=lesson, task_id=task_id)
    return JsonResponse({"ok": True})


@login_required
@require_POST
def lesson_toggle_check(request, lesson_id, check_id):
    lesson = _owned_lesson_or_404(request, lesson_id)
    data = json.loads(request.body or "{}")
    ChecklistCheck.objects.update_or_create(
        lesson=lesson, check_id=check_id[:32], defaults={"is_checked": bool(data.get("checked"))}
    )
    return JsonResponse({"ok": True})


# --------------------------------------------------------------- staff tool --

@staff_member_required
def lesson_preview(request):
    """Paste a lesson document and see it rendered exactly as a student would.
    Nothing here touches the database — a scratch tool for checking a file
    parses cleanly before filing it under a real student."""
    if request.method == "POST":
        raw = request.POST.get("markdown", "")
        parsed = parse_lesson(raw)
        context = _document_context(
            parsed, preview_warnings=parsed.warnings, preview_markdown=raw,
            back_to_editor_url=reverse("lesson_preview"),
        )
        return render(request, "learning/lesson/document.html", context)

    raw = SAMPLE_LESSON_PATH.read_text(encoding="utf-8") if SAMPLE_LESSON_PATH.exists() else ""
    return render(request, "learning/lesson_preview.html", {"markdown": raw})


# --------------------------------------------------------------- tutor view --

@staff_member_required
def student_list(request):
    """Every registered student, tutor or not — this is the roster, not a
    curated list, so a new sign-up shows up here with no extra step."""
    profiles = StudentProfile.objects.select_related("user").order_by("display_name")
    rows = []
    for profile in profiles:
        lessons = Lesson.objects.filter(student=profile.user)
        rows.append({
            "profile": profile,
            "lesson_count": lessons.count(),
            "last_date": lessons.order_by("-date").values_list("date", flat=True).first(),
        })
    unlinked = User.objects.filter(student_profile__isnull=True, is_staff=False)
    return render(request, "learning/tutor/student_list.html", {"rows": rows, "unlinked": unlinked})


@staff_member_required
def student_create(request):
    """Turn a real account (one you created, or one someone signed up with)
    into a student — link it to a new StudentProfile. Also lets you create
    the account itself in the same step, for a student who has no login yet."""
    unlinked = User.objects.filter(student_profile__isnull=True, is_staff=False).order_by("username")
    generated_password = None
    error = None

    if request.method == "POST":
        existing_id = request.POST.get("existing_user")
        new_username = request.POST.get("new_username", "").strip()
        display_name = request.POST.get("display_name", "").strip()
        platform = request.POST.get("platform", "direct")
        is_minor = bool(request.POST.get("is_minor"))
        guardian_email = request.POST.get("guardian_email", "").strip()

        if not display_name:
            error = "Display name is required."
        elif existing_id:
            user = get_object_or_404(User, pk=existing_id, student_profile__isnull=True)
        elif new_username:
            if User.objects.filter(username=new_username).exists():
                error = f"The username '{new_username}' is already taken."
                user = None
            else:
                # Simple on purpose: a random password is one more thing for a
                # young student to forget. Defaults to the username itself —
                # easy to remember, change it later if that's too weak for a
                # given student.
                new_password = request.POST.get("new_password", "").strip()
                generated_password = new_password or new_username
                user = User.objects.create_user(new_username, password=generated_password)
        else:
            error = "Pick an existing account, or enter a username to create a new one."
            user = None

        if not error and user is not None:
            StudentProfile.objects.create(
                user=user, display_name=display_name, platform=platform,
                is_minor=is_minor, guardian_email=guardian_email,
            )
            if not generated_password:
                return redirect("student_detail", user_id=user.id)
            # Show the generated password once — it can't be recovered after this.
            return render(request, "learning/tutor/student_created.html", {
                "user": user, "password": generated_password,
            })

    return render(request, "learning/tutor/student_create.html", {
        "unlinked": unlinked, "error": error,
    })


@staff_member_required
def student_detail(request, user_id):
    student = get_object_or_404(User, pk=user_id)
    profile = getattr(student, "student_profile", None)

    if request.method == "POST" and request.POST.get("action") == "save_profile" and profile:
        profile.notes = request.POST.get("notes", "")
        profile.save(update_fields=["notes"])
        return redirect("student_detail", user_id=student.id)

    lessons = Lesson.objects.filter(student=student).order_by("-date", "-id")
    courses = Course.objects.filter(enrollments__student=student, enrollments__is_active=True)
    return render(request, "learning/tutor/student_detail.html", {
        "student": student, "profile": profile, "lessons": lessons, "courses": courses,
    })


@staff_member_required
def lesson_upload(request, user_id, lesson_id=None):
    """Paste or upload a markdown lesson for one student — also doubles as
    the editor for an existing lesson when lesson_id is given (title, dates,
    tasks, anything in the document can change). Two-step: this view always
    shows a preview first; nothing saves until 'Confirm & save' posts back
    here with action=confirm. The student is locked to the URL, so a
    front-matter mismatch is caught rather than silently filed."""
    student = get_object_or_404(User, pk=user_id)
    editing_lesson = None
    if lesson_id is not None:
        editing_lesson = get_object_or_404(Lesson, pk=lesson_id, student=student)

    editor_url = (
        reverse("lesson_edit", args=[student.id, editing_lesson.id]) if editing_lesson
        else reverse("lesson_upload", args=[student.id])
    )

    if request.method != "POST":
        markdown = editing_lesson.markdown_source if editing_lesson else ""
        return render(request, "learning/tutor/lesson_upload.html", {
            "student": student, "markdown": markdown, "editing_lesson": editing_lesson,
        })

    raw = request.POST.get("markdown", "")
    upload = request.FILES.get("file")
    if upload:
        raw = upload.read().decode("utf-8", errors="replace")

    parsed = parse_lesson(raw)
    try:
        plan = resolve_save_plan(parsed, locked_student=student, target_lesson=editing_lesson)
        error = None
    except LessonSaveError as e:
        plan = None
        error = e.message

    if request.POST.get("action") == "confirm" and plan is not None:
        lesson = save_lesson(parsed, raw, plan)
        return redirect("lesson_tutor_view", lesson_id=lesson.id)

    context = _document_context(
        parsed, preview_warnings=None, preview_markdown=raw, back_to_editor_url=editor_url,
    )
    context.update({
        "student": student, "markdown": raw, "plan": plan, "error": error, "editing_lesson": editing_lesson,
    })
    return render(request, "learning/tutor/lesson_upload_preview.html", context)


@staff_member_required
@require_POST
def lesson_delete(request, lesson_id):
    """Permanent — the confirm dialog is client-side (see the template), and
    that's the only guard, so this is not exposed anywhere but a deliberate
    tutor click. Everything under it (tasks, saved answers, reveal log)
    cascades with it."""
    lesson = get_object_or_404(Lesson, pk=lesson_id)
    student_id = lesson.student_id
    lesson.delete()
    return redirect("student_detail", user_id=student_id)


@staff_member_required
def lesson_tutor_view(request, lesson_id):
    """Read-only: every saved blank, every checkbox, every task's completion
    state and the full reveal log with timestamps — the most useful signal
    for spotting where a student actually struggled."""
    lesson = get_object_or_404(Lesson.objects.select_related("student", "course"), pk=lesson_id)
    if not lesson.is_document:
        raise Http404
    parsed = parse_lesson(lesson.markdown_source)
    context = _document_context(parsed, lesson=lesson, can_edit=False)
    context["lesson"] = lesson
    context["reveals"] = HintReveal.objects.filter(lesson=lesson).order_by("-revealed_at")
    return render(request, "learning/tutor/lesson_tutor_view.html", context)


@staff_member_required
@require_POST
def lesson_toggle_lock(request, lesson_id):
    lesson = get_object_or_404(Lesson, pk=lesson_id)
    lesson.is_published = not lesson.is_published
    lesson.save(update_fields=["is_published"])
    return redirect("lesson_tutor_view", lesson_id=lesson.id)

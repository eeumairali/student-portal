import json

from django.conf import settings
from django.contrib.auth.models import User
from django.core.files.base import ContentFile
from django.test import TestCase
from django.urls import reverse

from accounts.models import StudentProfile
from learning.lesson_markdown import parse_lesson
from learning.models import Course, Enrollment, HintReveal, Lesson, LessonFile, LessonProgress, Task

LESSON_TEMPLATE_PATH = settings.BASE_DIR / "skills" / "LESSON_TEMPLATE.md"
W5D1_KMEANS_PATH = settings.BASE_DIR / "skills" / "W5D1_KMEANS.md"

SIMPLE_LESSON_MD = """---
student: {student}
date: 2026-01-10
title: {title}
visible: true
---

## First block

Intro text.

:::example
```python
print("hi")
```
:::

:::practice id=t1 hint=5
Do the thing.

EXPECTED
hi

SOLUTION
```python
print("hi")
```
:::

## Second block

:::practice id=q1
Pick a number and print it.
:::
"""


class PortalTests(TestCase):
    def setUp(self):
        self.alex = User.objects.create_user("alex", password="pw-alex-12345")
        self.priya = User.objects.create_user("priya", password="pw-priya-12345")
        self.course = Course.objects.create(title="Python", slug="python")
        self.lesson = Lesson.objects.create(course=self.course, order=1, title="Variables")
        self.file = LessonFile.objects.create(
            lesson=self.lesson, label="Notebook",
            upload=ContentFile(b"print('hi')", name="l1.ipynb"),
        )
        Enrollment.objects.create(student=self.alex, course=self.course)

    def test_login_required(self):
        for url in [reverse("dashboard"),
                    reverse("lesson_detail", args=[self.lesson.id]),
                    reverse("lesson_file", args=[self.file.id])]:
            self.assertEqual(self.client.get(url).status_code, 302, url)

    def test_enrolled_student_sees_course_and_file(self):
        self.client.force_login(self.alex)
        self.assertContains(self.client.get(reverse("dashboard")), "Python")
        response = self.client.get(reverse("lesson_file", args=[self.file.id]))
        self.assertEqual(response.status_code, 200)
        self.assertIn("l1.ipynb", response["Content-Disposition"])

    def test_other_student_cannot_reach_course_lesson_or_file(self):
        self.client.force_login(self.priya)
        self.assertNotContains(self.client.get(reverse("dashboard")), "Python")
        for url in [reverse("course_detail", args=[self.course.slug]),
                    reverse("lesson_detail", args=[self.lesson.id]),
                    reverse("lesson_file", args=[self.file.id])]:
            self.assertEqual(self.client.get(url).status_code, 404, url)

    def test_toggle_updates_progress_and_percentage(self):
        Lesson.objects.create(course=self.course, order=2, title="Loops")
        self.client.force_login(self.alex)
        url = reverse("toggle_lesson", args=[self.lesson.id])
        response = self.client.post(url, HTTP_HX_REQUEST="true")
        self.assertContains(response, "50%")
        self.assertTrue(LessonProgress.objects.get(student=self.alex, lesson=self.lesson).is_complete)
        self.client.post(url, HTTP_HX_REQUEST="true")
        self.assertFalse(LessonProgress.objects.get(student=self.alex, lesson=self.lesson).is_complete)

    def test_other_student_cannot_toggle(self):
        self.client.force_login(self.priya)
        self.assertEqual(
            self.client.post(reverse("toggle_lesson", args=[self.lesson.id])).status_code, 404
        )
        self.assertFalse(LessonProgress.objects.filter(student=self.priya).exists())

    def test_upload_path_is_not_guessable(self):
        self.assertNotIn("l1", self.file.upload.name)
        self.assertEqual(self.file.original_name, "l1.ipynb")


class LessonMarkdownParserTests(TestCase):
    """LESSON_TEMPLATE.md is the format's own worked example and doubles as
    the parser's test fixture — see skills/FORMAT_SPEC.md."""

    def setUp(self):
        self.raw = LESSON_TEMPLATE_PATH.read_text(encoding="utf-8")

    def test_parses_with_no_warnings(self):
        parsed = parse_lesson(self.raw)
        self.assertEqual(parsed.warnings, [])

    def test_front_matter_known_and_unknown_keys(self):
        parsed = parse_lesson(self.raw)
        self.assertEqual(parsed.front_matter["student"], "student_username")
        self.assertEqual(parsed.front_matter["title"], "Lesson title")
        self.assertEqual(parsed.meta, {})

    def test_two_blocks_numbered_and_two_practices_found(self):
        parsed = parse_lesson(self.raw)
        self.assertEqual(len(parsed.blocks), 2)
        self.assertEqual([b.index for b in parsed.blocks], [1, 2])
        self.assertEqual([b.total for b in parsed.blocks], [2, 2])
        self.assertEqual([p.practice_id for p in parsed.practices], ["p1", "p2"])

    def test_practice_with_solution_has_hint_seconds(self):
        parsed = parse_lesson(self.raw)
        p1 = next(p for p in parsed.practices if p.practice_id == "p1")
        self.assertTrue(p1.has_solution)
        self.assertEqual(p1.hint_seconds, 20)

    def test_missing_required_fields_produce_warnings(self):
        parsed = parse_lesson("---\ntitle: No student or date\n---\n## Block\nBody text.")
        self.assertIn("Missing required field: student", parsed.warnings)
        self.assertIn("Missing required field: date", parsed.warnings)

    def test_topics_are_collected_as_a_list(self):
        raw = "---\nstudent: andy\ndate: 2026-01-01\ntitle: t\ntopics:\n  - Alpha\n  - Beta\n---\n## Block\nBody.\n"
        parsed = parse_lesson(raw)
        self.assertEqual(parsed.topics, ["Alpha", "Beta"])

    def test_practice_without_solution_has_no_hint(self):
        raw = "---\nstudent: andy\ndate: 2026-01-01\ntitle: t\n---\n## Block\n:::practice id=p1\nJust try it.\n:::\n"
        parsed = parse_lesson(raw)
        p1 = parsed.practices[0]
        self.assertFalse(p1.has_solution)
        self.assertIsNone(p1.solution_html)

    def test_w5d1_kmeans_parses_with_example_and_two_practices(self):
        parsed = parse_lesson(W5D1_KMEANS_PATH.read_text(encoding="utf-8"))
        self.assertEqual(parsed.warnings, [])
        self.assertEqual(len(parsed.practices), 2)


class LessonPreviewViewTests(TestCase):
    """The staff-only paste/preview page. No persistence yet — this just
    proves the parser and renderer work end to end on the real fixture."""

    def setUp(self):
        self.raw = LESSON_TEMPLATE_PATH.read_text(encoding="utf-8")
        self.staff = User.objects.create_user("tutor", password="pw-tutor-12345", is_staff=True)
        self.student = User.objects.create_user("alex", password="pw-alex-12345")

    def test_anonymous_redirected_to_login(self):
        response = self.client.get(reverse("lesson_preview"))
        self.assertEqual(response.status_code, 302)

    def test_non_staff_student_cannot_reach_preview(self):
        self.client.force_login(self.student)
        response = self.client.get(reverse("lesson_preview"))
        self.assertEqual(response.status_code, 302)

    def test_staff_sees_paste_form_prefilled_with_sample(self):
        self.client.force_login(self.staff)
        response = self.client.get(reverse("lesson_preview"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Lesson title")

    def test_staff_can_render_the_full_template_end_to_end(self):
        self.client.force_login(self.staff)
        response = self.client.post(reverse("lesson_preview"), {"markdown": self.raw})
        self.assertEqual(response.status_code, 200)
        content = response.content.decode()
        self.assertIn('data-task-id="p1"', content)
        self.assertIn('data-task-id="p2"', content)
        self.assertIn("Solution", content)
        self.assertIn("static/js/lesson.js", content)
        self.assertNotIn("Preview warnings", content)

    def test_invalid_markdown_shows_warnings_not_a_crash(self):
        self.client.force_login(self.staff)
        response = self.client.post(reverse("lesson_preview"), {"markdown": "no front matter here"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Preview warnings")


class TutorUploadFlowTests(TestCase):
    """The end-to-end path: paste/upload -> preview -> confirm -> saved lesson,
    with reconciliation on re-upload and access control on the write endpoints."""

    def setUp(self):
        self.staff = User.objects.create_user("tutor2", password="pw-tutor-12345", is_staff=True)
        self.andy = User.objects.create_user("andy", password="pw-andy-123456")
        self.priya = User.objects.create_user("priya", password="pw-priya-123456")
        StudentProfile.objects.create(user=self.andy, display_name="Andy")
        StudentProfile.objects.create(user=self.priya, display_name="Priya")

    def test_student_list_requires_staff(self):
        self.client.force_login(self.andy)
        self.assertEqual(self.client.get(reverse("student_list")).status_code, 302)

    def test_student_list_shows_every_registered_student(self):
        self.client.force_login(self.staff)
        response = self.client.get(reverse("student_list"))
        self.assertContains(response, "Andy")
        self.assertContains(response, "Priya")

    def test_upload_preview_does_not_save(self):
        self.client.force_login(self.staff)
        md = SIMPLE_LESSON_MD.format(student="andy", title="First note")
        response = self.client.post(reverse("lesson_upload", args=[self.andy.id]), {"markdown": md})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Lesson.objects.count(), 0)
        self.assertContains(response, "Confirm")

    def test_confirm_saves_lesson_and_practices(self):
        self.client.force_login(self.staff)
        md = SIMPLE_LESSON_MD.format(student="andy", title="First note")
        response = self.client.post(
            reverse("lesson_upload", args=[self.andy.id]), {"markdown": md, "action": "confirm"}
        )
        lesson = Lesson.objects.get(student=self.andy, title="First note")
        self.assertRedirects(response, reverse("lesson_tutor_view", args=[lesson.id]))
        self.assertEqual(lesson.tasks.count(), 2)
        self.assertTrue(lesson.is_published)  # visible: true in the fixture

    def test_mismatched_student_in_front_matter_is_rejected(self):
        self.client.force_login(self.staff)
        md = SIMPLE_LESSON_MD.format(student="priya", title="Wrong kid")
        response = self.client.post(
            reverse("lesson_upload", args=[self.andy.id]), {"markdown": md, "action": "confirm"}
        )
        self.assertEqual(Lesson.objects.count(), 0)
        self.assertContains(response, "uploading it on")

    def test_unknown_student_username_is_rejected(self):
        self.client.force_login(self.staff)
        md = SIMPLE_LESSON_MD.format(student="nobody", title="Ghost")
        response = self.client.post(
            reverse("lesson_upload", args=[self.andy.id]), {"markdown": md, "action": "confirm"}
        )
        self.assertEqual(Lesson.objects.count(), 0)
        self.assertContains(response, "No student with username")

    def test_reuploading_same_lesson_updates_not_duplicates(self):
        self.client.force_login(self.staff)
        md = SIMPLE_LESSON_MD.format(student="andy", title="Same note")
        self.client.post(reverse("lesson_upload", args=[self.andy.id]), {"markdown": md, "action": "confirm"})
        self.client.post(reverse("lesson_upload", args=[self.andy.id]), {"markdown": md, "action": "confirm"})
        self.assertEqual(Lesson.objects.filter(student=self.andy, title="Same note").count(), 1)

    def test_removing_a_practice_orphans_it_and_warns_if_student_has_progress(self):
        self.client.force_login(self.staff)
        md = SIMPLE_LESSON_MD.format(student="andy", title="Reconcile me")
        self.client.post(reverse("lesson_upload", args=[self.andy.id]), {"markdown": md, "action": "confirm"})
        lesson = Lesson.objects.get(student=self.andy, title="Reconcile me")

        self.client.force_login(self.andy)
        self.client.post(
            reverse("lesson_toggle_task", args=[lesson.id, "q1"]),
            data=json.dumps({"complete": True}), content_type="application/json",
        )

        shorter_md = md.split("## Second block")[0]
        self.client.force_login(self.staff)
        preview = self.client.post(reverse("lesson_upload", args=[self.andy.id]), {"markdown": shorter_md})
        self.assertContains(preview, "removed")
        self.assertContains(preview, "has progress")

        self.client.post(reverse("lesson_upload", args=[self.andy.id]), {"markdown": shorter_md, "action": "confirm"})
        task = Task.objects.get(lesson=lesson, task_id="q1")
        self.assertTrue(task.is_orphaned)
        self.assertTrue(task.is_complete)  # never lost, just hidden

    def test_lock_unlock_hides_lesson_from_student(self):
        self.client.force_login(self.staff)
        md = SIMPLE_LESSON_MD.format(student="andy", title="Lockable")
        self.client.post(reverse("lesson_upload", args=[self.andy.id]), {"markdown": md, "action": "confirm"})
        lesson = Lesson.objects.get(student=self.andy, title="Lockable")
        self.assertTrue(lesson.is_published)

        self.client.post(reverse("lesson_toggle_lock", args=[lesson.id]))
        lesson.refresh_from_db()
        self.assertFalse(lesson.is_published)

        self.client.force_login(self.andy)
        self.assertEqual(self.client.get(reverse("lesson_detail", args=[lesson.id])).status_code, 404)

        self.client.force_login(self.staff)
        self.assertEqual(self.client.get(reverse("lesson_detail", args=[lesson.id])).status_code, 200)

    def test_uploading_a_session_under_a_course_auto_enrols_the_student(self):
        self.client.force_login(self.staff)
        md = SIMPLE_LESSON_MD.format(student="andy", title="Course session")
        md = md.replace("visible: true\n---", "visible: true\ncourse: test-course\n---")
        self.assertFalse(Enrollment.objects.filter(student=self.andy).exists())

        self.client.post(reverse("lesson_upload", args=[self.andy.id]), {"markdown": md, "action": "confirm"})

        course = Course.objects.get(slug="test-course")
        self.assertTrue(Enrollment.objects.filter(student=self.andy, course=course, is_active=True).exists())

    def test_two_students_under_the_same_course_cannot_see_each_others_sessions(self):
        self.client.force_login(self.staff)
        for username, title in [("andy", "Andy's session"), ("priya", "Priya's session")]:
            md = SIMPLE_LESSON_MD.format(student=username, title=title)
            md = md.replace("visible: true\n---", "visible: true\ncourse: shared-course\n---")
            self.client.post(reverse("lesson_upload", args=[getattr(self, username).id]), {"markdown": md, "action": "confirm"})

        from learning.services import course_progress
        course = Course.objects.get(slug="shared-course")

        andy_view = course_progress(self.andy, course)
        titles = [l.title for l in andy_view["document_lessons"]]
        self.assertIn("Andy's session", titles)
        self.assertNotIn("Priya's session", titles)

        priya_view = course_progress(self.priya, course)
        titles = [l.title for l in priya_view["document_lessons"]]
        self.assertIn("Priya's session", titles)
        self.assertNotIn("Andy's session", titles)

        # and the page itself, not just the service function
        self.client.force_login(self.andy)
        response = self.client.get(reverse("course_detail", args=["shared-course"]))
        self.assertContains(response, "Andy&#x27;s session")
        self.assertNotContains(response, "Priya&#x27;s session")


class LessonEditDeleteTests(TestCase):
    """A tutor can edit an existing note (including renaming it, which must
    update the same row rather than being treated as a new lesson) and
    permanently delete one."""

    def setUp(self):
        self.staff = User.objects.create_user("tutor5", password="pw-tutor-12345", is_staff=True)
        self.andy = User.objects.create_user("andy4", password="pw-andy-123456")
        self.priya = User.objects.create_user("priya4", password="pw-priya-123456")
        StudentProfile.objects.create(user=self.andy, display_name="Andy4")
        StudentProfile.objects.create(user=self.priya, display_name="Priya4")

        self.client.force_login(self.staff)
        md = SIMPLE_LESSON_MD.format(student="andy4", title="Original title")
        self.client.post(reverse("lesson_upload", args=[self.andy.id]), {"markdown": md, "action": "confirm"})
        self.lesson = Lesson.objects.get(student=self.andy, title="Original title")
        self.client.logout()

    def test_edit_page_prefills_existing_markdown(self):
        self.client.force_login(self.staff)
        response = self.client.get(reverse("lesson_edit", args=[self.andy.id, self.lesson.id]))
        self.assertContains(response, "Original title")
        self.assertContains(response, "andy4")

    def test_renaming_the_title_updates_the_same_lesson_not_a_duplicate(self):
        self.client.force_login(self.staff)
        new_md = SIMPLE_LESSON_MD.format(student="andy4", title="Renamed title")
        response = self.client.post(
            reverse("lesson_edit", args=[self.andy.id, self.lesson.id]),
            {"markdown": new_md, "action": "confirm"},
        )
        self.assertRedirects(response, reverse("lesson_tutor_view", args=[self.lesson.id]))
        self.assertEqual(Lesson.objects.filter(student=self.andy).count(), 1)
        self.lesson.refresh_from_db()
        self.assertEqual(self.lesson.title, "Renamed title")

    def test_edit_preserves_student_progress_on_unchanged_practices(self):
        self.client.force_login(self.andy)
        self.client.post(
            reverse("lesson_toggle_task", args=[self.lesson.id, "t1"]),
            data=json.dumps({"complete": True}), content_type="application/json",
        )
        self.client.force_login(self.staff)
        new_md = SIMPLE_LESSON_MD.format(student="andy4", title="Retitled, practice kept")
        self.client.post(
            reverse("lesson_edit", args=[self.andy.id, self.lesson.id]),
            {"markdown": new_md, "action": "confirm"},
        )
        self.assertTrue(Task.objects.get(lesson=self.lesson, task_id="t1").is_complete)

    def test_edit_requires_staff(self):
        self.client.force_login(self.andy)
        response = self.client.get(reverse("lesson_edit", args=[self.andy.id, self.lesson.id]))
        self.assertEqual(response.status_code, 302)

    def test_cannot_edit_another_students_lesson_via_a_guessed_url(self):
        self.client.force_login(self.staff)
        response = self.client.get(reverse("lesson_edit", args=[self.priya.id, self.lesson.id]))
        self.assertEqual(response.status_code, 404)

    def test_delete_removes_lesson_and_cascades(self):
        self.client.force_login(self.andy)
        self.client.post(
            reverse("lesson_toggle_task", args=[self.lesson.id, "t1"]),
            data=json.dumps({"complete": True}), content_type="application/json",
        )
        self.client.force_login(self.staff)
        response = self.client.post(reverse("lesson_delete", args=[self.lesson.id]))
        self.assertRedirects(response, reverse("student_detail", args=[self.andy.id]))
        self.assertFalse(Lesson.objects.filter(pk=self.lesson.id).exists())
        self.assertFalse(Task.objects.filter(lesson_id=self.lesson.id).exists())

    def test_delete_requires_staff(self):
        self.client.force_login(self.andy)
        response = self.client.post(reverse("lesson_delete", args=[self.lesson.id]))
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Lesson.objects.filter(pk=self.lesson.id).exists())

    def test_delete_requires_post(self):
        self.client.force_login(self.staff)
        response = self.client.get(reverse("lesson_delete", args=[self.lesson.id]))
        self.assertEqual(response.status_code, 405)
        self.assertTrue(Lesson.objects.filter(pk=self.lesson.id).exists())


class StudentCreateTests(TestCase):
    """Turning a real account (created ahead of time, with no StudentProfile
    yet) into a student, and creating a brand-new account in the same step."""

    def setUp(self):
        self.staff = User.objects.create_user("tutor4", password="pw-tutor-12345", is_staff=True)
        self.bare_account = User.objects.create_user("andy3", password="whatever-123")

    def test_requires_staff(self):
        self.client.force_login(self.bare_account)
        self.assertEqual(self.client.get(reverse("student_create")).status_code, 302)

    def test_unlinked_account_appears_as_a_link_candidate(self):
        self.client.force_login(self.staff)
        response = self.client.get(reverse("student_create"))
        self.assertContains(response, "andy3")

    def test_linking_an_existing_account_creates_a_profile_not_a_new_user(self):
        self.client.force_login(self.staff)
        before = User.objects.count()
        response = self.client.post(reverse("student_create"), {
            "existing_user": self.bare_account.id, "display_name": "Andy", "platform": "direct",
        })
        self.assertRedirects(response, reverse("student_detail", args=[self.bare_account.id]))
        self.assertEqual(User.objects.count(), before)
        profile = StudentProfile.objects.get(user=self.bare_account)
        self.assertEqual(profile.display_name, "Andy")

    def test_creating_a_brand_new_account_defaults_password_to_username(self):
        self.client.force_login(self.staff)
        response = self.client.post(reverse("student_create"), {
            "new_username": "brand_new_student", "display_name": "Sam", "platform": "preply",
        })
        self.assertEqual(response.status_code, 200)
        user = User.objects.get(username="brand_new_student")
        self.assertTrue(StudentProfile.objects.filter(user=user).exists())
        self.assertContains(response, "brand_new_student")
        self.assertTrue(user.check_password("brand_new_student"))

    def test_creating_a_brand_new_account_with_explicit_password(self):
        self.client.force_login(self.staff)
        self.client.post(reverse("student_create"), {
            "new_username": "chosen_pw_student", "new_password": "hunter2",
            "display_name": "Sam", "platform": "preply",
        })
        user = User.objects.get(username="chosen_pw_student")
        self.assertTrue(user.check_password("hunter2"))

    def test_minor_without_guardian_email_is_allowed(self):
        self.client.force_login(self.staff)
        response = self.client.post(reverse("student_create"), {
            "existing_user": self.bare_account.id, "display_name": "Andy", "is_minor": "on",
        })
        self.assertRedirects(response, reverse("student_detail", args=[self.bare_account.id]))
        profile = StudentProfile.objects.get(user=self.bare_account)
        self.assertTrue(profile.is_minor)
        self.assertEqual(profile.guardian_email, "")


class StudentSavesOwnProgressTests(TestCase):
    """A student may write their own practice completions/reveals — never a
    tutor's, never another student's, even via a guessed lesson id."""

    def setUp(self):
        self.staff = User.objects.create_user("tutor3", password="pw-tutor-12345", is_staff=True)
        self.andy = User.objects.create_user("andy2", password="pw-andy-123456")
        self.priya = User.objects.create_user("priya2", password="pw-priya-123456")
        StudentProfile.objects.create(user=self.andy, display_name="Andy2")
        StudentProfile.objects.create(user=self.priya, display_name="Priya2")

        self.client.force_login(self.staff)
        md = SIMPLE_LESSON_MD.format(student="andy2", title="Progress test")
        self.client.post(reverse("lesson_upload", args=[self.andy.id]), {"markdown": md, "action": "confirm"})
        self.lesson = Lesson.objects.get(student=self.andy, title="Progress test")
        self.client.logout()

    def test_owner_can_mark_a_practice_done(self):
        self.client.force_login(self.andy)
        response = self.client.post(
            reverse("lesson_toggle_task", args=[self.lesson.id, "t1"]),
            data=json.dumps({"complete": True}), content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(Task.objects.get(lesson=self.lesson, task_id="t1").is_complete)

    def test_other_student_cannot_toggle_task(self):
        self.client.force_login(self.priya)
        response = self.client.post(
            reverse("lesson_toggle_task", args=[self.lesson.id, "t1"]),
            data=json.dumps({"complete": True}), content_type="application/json",
        )
        self.assertEqual(response.status_code, 404)

    def test_reveal_is_logged_with_timestamp(self):
        self.client.force_login(self.andy)
        self.client.post(reverse("lesson_reveal_hint", args=[self.lesson.id, "t1"]), data="{}", content_type="application/json")
        self.assertEqual(HintReveal.objects.filter(lesson=self.lesson, task_id="t1").count(), 1)

    def test_tutor_view_shows_saved_state_and_is_staff_only(self):
        self.client.force_login(self.andy)
        self.client.post(
            reverse("lesson_toggle_task", args=[self.lesson.id, "t1"]),
            data=json.dumps({"complete": True}), content_type="application/json",
        )
        self.client.logout()

        self.client.force_login(self.priya)
        self.assertEqual(self.client.get(reverse("lesson_tutor_view", args=[self.lesson.id])).status_code, 302)

        self.client.force_login(self.staff)
        response = self.client.get(reverse("lesson_tutor_view", args=[self.lesson.id]))
        self.assertEqual(response.status_code, 200)


from django.test import override_settings  # noqa: E402

# Static files are hashed only in production; tests run against plain storage.
PortalTests = override_settings(
    STORAGES={
        "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
        "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
    }
)(PortalTests)

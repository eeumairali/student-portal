"""Creates a demo tutor, two demo students and one course with real files,
so you can see the portal working straight after install.

    python manage.py seed_demo

Safe to re-run. Demo accounts are prefixed 'demo_' — delete them in the admin
before you go live.
"""
import io

from django.contrib.auth.models import User
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand

from accounts.models import StudentProfile
from learning.models import Course, Enrollment, Lesson, LessonFile

NOTEBOOK = """{
 "cells": [
  {"cell_type": "markdown", "metadata": {}, "source": ["# Lesson 1 - variables\\n", "Fill in each TODO."]},
  {"cell_type": "code", "execution_count": null, "metadata": {}, "outputs": [],
   "source": ["# TODO: store your name in a variable called name\\n", "\\n", "# Expected: Hello, <your name>\\n"]}
 ],
 "metadata": {"kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"}},
 "nbformat": 4, "nbformat_minor": 5
}"""

CSV = "player,goals,assists\nSalah,18,9\nHaaland,27,5\nSaka,12,11\nPalmer,15,8\n"


class Command(BaseCommand):
    help = "Create a demo course, lessons, files and two demo students."

    def handle(self, *args, **options):
        tutor, made = User.objects.get_or_create(
            username="demo_tutor", defaults={"is_staff": True, "is_superuser": True}
        )
        if made:
            tutor.set_password("demo-tutor-pass")
            tutor.save()
            self.stdout.write("Tutor login: demo_tutor / demo-tutor-pass")

        course, _ = Course.objects.update_or_create(
            slug="python-foundations",
            defaults={
                "title": "Python foundations",
                "subject": "python",
                "description": "Eight sessions from your first variable to a small program you build yourself.",
            },
        )

        lessons = [
            ("Variables and printing", "Store values, name them well, and show them on screen."),
            ("Lists and loops", "Hold many values at once and do something with each one."),
            ("Conditions", "Make your program choose between two paths."),
            ("Functions", "Wrap working code in a name so you can reuse it."),
        ]
        for i, (title, desc) in enumerate(lessons, start=1):
            lesson, _ = Lesson.objects.update_or_create(
                course=course, order=i, defaults={"title": title, "description": desc}
            )
            if i == 1 and not lesson.files.exists():
                LessonFile.objects.create(
                    lesson=lesson, label="Lesson 1 practice notebook", kind="notebook",
                    upload=ContentFile(NOTEBOOK.encode(), name="lesson_01_variables.ipynb"),
                )
                LessonFile.objects.create(
                    lesson=lesson, label="Football stats dataset", kind="dataset",
                    upload=ContentFile(CSV.encode(), name="football_stats.csv"),
                )

        for username, display, minor in [
            ("demo_student", "Alex", True),
            ("demo_student2", "Priya", False),
        ]:
            student, made = User.objects.get_or_create(username=username)
            if made:
                student.set_password("demo-student-pass")
                student.save()
            StudentProfile.objects.update_or_create(
                user=student,
                defaults={
                    "display_name": display,
                    "platform": "direct",
                    "is_minor": minor,
                    "guardian_email": "parent@example.com" if minor else "",
                },
            )
            Enrollment.objects.get_or_create(student=student, course=course)

        self.stdout.write(self.style.SUCCESS(
            "Seeded. Student login: demo_student / demo-student-pass  "
            "(demo_student2 is enrolled too, so you can check they cannot see each other.)"
        ))

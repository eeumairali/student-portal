from django.contrib import admin
from django.utils.html import format_html

from .models import (
    BlankAnswer, ChecklistCheck, Course, Enrollment, HintReveal, Lesson, LessonFile, LessonProgress, Task,
)


class LessonFileInline(admin.TabularInline):
    model = LessonFile
    extra = 2
    fields = ("label", "kind", "upload", "uploaded_at")
    readonly_fields = ("uploaded_at",)


class LessonInline(admin.TabularInline):
    model = Lesson
    extra = 1
    fields = ("order", "title", "is_published")
    show_change_link = True
    ordering = ("order",)


class EnrollmentInline(admin.TabularInline):
    model = Enrollment
    extra = 1
    autocomplete_fields = ("student",)


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ("title", "subject", "lesson_count", "student_count", "is_published")
    list_filter = ("subject", "is_published")
    search_fields = ("title", "description")
    prepopulated_fields = {"slug": ("title",)}
    inlines = [LessonInline, EnrollmentInline]

    @admin.display(description="Lessons")
    def lesson_count(self, obj):
        return obj.lessons.count()

    @admin.display(description="Students")
    def student_count(self, obj):
        return obj.enrollments.filter(is_active=True).count()


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ("title", "student", "date", "course", "order", "file_count", "is_published")
    list_filter = ("course", "is_published", "theme")
    search_fields = ("title", "description", "student__username")
    autocomplete_fields = ("student", "course")
    inlines = [LessonFileInline]
    fieldsets = (
        (None, {"fields": ("course", "order", "title", "is_published")}),
        ("What the student sees (legacy shared lessons)", {"fields": ("description",)}),
        ("Dated document (Phase 2 — normally added via the Students page, not here)", {
            "classes": ("collapse",),
            "fields": ("student", "date", "subtitle", "theme", "hint_seconds_default", "meta", "markdown_source"),
        }),
    )

    @admin.display(description="Files")
    def file_count(self, obj):
        return obj.files.count()


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ("lesson", "task_id", "type", "is_complete", "is_orphaned", "completed_at")
    list_filter = ("type", "is_complete", "is_orphaned")
    search_fields = ("task_id", "lesson__title", "lesson__student__username")
    autocomplete_fields = ("lesson",)


@admin.register(BlankAnswer)
class BlankAnswerAdmin(admin.ModelAdmin):
    list_display = ("lesson", "blank_id", "value", "updated_at")
    search_fields = ("blank_id", "lesson__title", "lesson__student__username")
    autocomplete_fields = ("lesson",)


@admin.register(ChecklistCheck)
class ChecklistCheckAdmin(admin.ModelAdmin):
    list_display = ("lesson", "check_id", "is_checked", "updated_at")
    autocomplete_fields = ("lesson",)


@admin.register(HintReveal)
class HintRevealAdmin(admin.ModelAdmin):
    list_display = ("lesson", "task_id", "revealed_at")
    search_fields = ("task_id", "lesson__title", "lesson__student__username")
    autocomplete_fields = ("lesson",)


@admin.register(LessonFile)
class LessonFileAdmin(admin.ModelAdmin):
    list_display = ("label", "lesson", "kind", "original_name", "pretty_size", "uploaded_at")
    list_filter = ("kind", "lesson__course")
    search_fields = ("label", "original_name")
    readonly_fields = ("original_name", "size_bytes", "uploaded_at", "secure_link")

    @admin.display(description="Student download link")
    def secure_link(self, obj):
        if not obj.pk:
            return "Save first."
        return format_html('<a href="/file/{}/">Download as a student would</a>', obj.pk)


@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ("student", "course", "started_on", "is_active")
    list_filter = ("course", "is_active")
    autocomplete_fields = ("student", "course")
    search_fields = ("student__username", "student__student_profile__display_name")


@admin.register(LessonProgress)
class LessonProgressAdmin(admin.ModelAdmin):
    list_display = ("student", "lesson", "is_complete", "completed_at")
    list_filter = ("is_complete", "lesson__course")
    readonly_fields = ("updated_at",)
    autocomplete_fields = ("student", "lesson")

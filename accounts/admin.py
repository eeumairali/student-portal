from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User

from .models import StudentComment, StudentProfile


class StudentProfileInline(admin.StackedInline):
    model = StudentProfile
    can_delete = False
    extra = 0
    fields = ("display_name", "platform", "is_minor", "guardian_email", "notes")


class UserAdmin(BaseUserAdmin):
    inlines = [StudentProfileInline]
    list_display = ("username", "get_display_name", "email", "is_staff", "last_login")

    @admin.display(description="Student")
    def get_display_name(self, obj):
        profile = getattr(obj, "student_profile", None)
        return profile.display_name if profile else "—"


admin.site.unregister(User)
admin.site.register(User, UserAdmin)


@admin.register(StudentComment)
class StudentCommentAdmin(admin.ModelAdmin):
    list_display = ("profile", "created_at")
    search_fields = ("profile__display_name", "body")
    raw_id_fields = ("profile",)

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User

from .models import StudentProfile


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

from django.urls import path

from . import views

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("course/<slug:slug>/", views.course_detail, name="course_detail"),
    path("lesson/<int:lesson_id>/", views.lesson_detail, name="lesson_detail"),
    path("lesson/<int:lesson_id>/toggle/", views.toggle_lesson, name="toggle_lesson"),
    path("lesson/<int:lesson_id>/task/<str:task_id>/complete/", views.lesson_toggle_task, name="lesson_toggle_task"),
    path("lesson/<int:lesson_id>/task/<str:task_id>/reveal/", views.lesson_reveal_hint, name="lesson_reveal_hint"),
    path("file/<int:file_id>/", views.lesson_file, name="lesson_file"),
    path("preview/", views.lesson_preview, name="lesson_preview"),
    path("students/", views.student_list, name="student_list"),
    path("students/new/", views.student_create, name="student_create"),
    path("students/<int:user_id>/", views.student_detail, name="student_detail"),
    path("students/<int:user_id>/course/<int:course_id>/unenroll/", views.unenroll_course, name="unenroll_course"),
    path("students/<int:user_id>/upload/", views.lesson_upload, name="lesson_upload"),
    path("students/<int:user_id>/lesson/<int:lesson_id>/edit/", views.lesson_upload, name="lesson_edit"),
    path("tutor/lesson/<int:lesson_id>/", views.lesson_tutor_view, name="lesson_tutor_view"),
    path("tutor/lesson/<int:lesson_id>/lock/", views.lesson_toggle_lock, name="lesson_toggle_lock"),
    path("tutor/lesson/<int:lesson_id>/delete/", views.lesson_delete, name="lesson_delete"),
]

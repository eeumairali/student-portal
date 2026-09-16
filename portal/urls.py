from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import include, path

from accounts.views import set_theme_palette

admin.site.site_header = "Student portal"
admin.site.site_title = "Student portal"
admin.site.index_title = "Courses, lessons and students"

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/theme-palette/", set_theme_palette, name="set_theme_palette"),
    path("accounts/login/", auth_views.LoginView.as_view(redirect_authenticated_user=True), name="login"),
    path("accounts/logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("accounts/password_change/", auth_views.PasswordChangeView.as_view(
        success_url="/accounts/password_change/done/"), name="password_change"),
    path("accounts/password_change/done/", auth_views.PasswordChangeDoneView.as_view(),
         name="password_change_done"),
    path("dashboard/", include("learning.urls")),
    path("", include("tutorials.urls")),
]

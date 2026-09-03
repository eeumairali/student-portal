from django.urls import path

from . import views

urlpatterns = [
    # public
    path("", views.home, name="home"),
    path("domain/<slug:slug>/", views.domain_detail, name="domain_detail"),
    path("t/<slug:slug>/", views.tutorial_detail, name="tutorial_detail"),

    # staff-only authoring tool, alongside the rest of the logged-in app
    path("dashboard/tutor/articles/", views.article_list, name="article_list"),
    path("dashboard/tutor/articles/new/", views.article_upload, name="article_upload"),
    path("dashboard/tutor/articles/<int:tutorial_id>/edit/", views.article_upload, name="article_edit"),
    path("dashboard/tutor/articles/<int:tutorial_id>/delete/", views.article_delete, name="article_delete"),
]

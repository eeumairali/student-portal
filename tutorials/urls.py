from django.urls import path

from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("domain/<slug:slug>/", views.domain_detail, name="domain_detail"),
    path("t/<slug:slug>/", views.tutorial_detail, name="tutorial_detail"),
]

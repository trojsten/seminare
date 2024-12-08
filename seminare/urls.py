import debug_toolbar
from django.contrib import admin
from django.shortcuts import render
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("seminare.problems.urls")),
    path("__debug__/", include(debug_toolbar.urls)),
    path("test/", lambda request: render(request, "test.html")),
]

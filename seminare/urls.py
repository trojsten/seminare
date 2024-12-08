import debug_toolbar
from django.contrib import admin
from django.shortcuts import render
from django.urls import include, path
from seminare.problems import urls as problems_urls

urlpatterns = [
    path("problems/", include(problems_urls)),
    path("admin/", admin.site.urls),
    path("", include("seminare.problems.urls")),
    path("__debug__/", include(debug_toolbar.urls)),
    path("test/", lambda request: render(request, "test.html")),
]

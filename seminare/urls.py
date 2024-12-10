import debug_toolbar
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.shortcuts import render
from django.urls import include, path

from seminare.problems import urls as problems_urls
from seminare.submits import urls as submits_urls

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("seminare.problems.urls")),
    path("", include("seminare.submits.urls")),
    path("__debug__/", include(debug_toolbar.urls)),
    path("test/", lambda request: render(request, "test.html")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

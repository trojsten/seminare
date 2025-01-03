import debug_toolbar
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.shortcuts import render
from django.urls import include, path, register_converter


class SubmitIDConverter:
    regex = "[FJT]-[0-9]+"

    def to_python(self, value):
        return value

    def to_url(self, value):
        return value


register_converter(SubmitIDConverter, "submit_id")

urlpatterns = [
    path("admin/", admin.site.urls),
    path("oidc/", include("mozilla_django_oidc.urls")),
    path("", include("seminare.problems.urls")),
    path("", include("seminare.submits.urls")),
    path("", include("seminare.content.urls")),
    path("org/", include("seminare.organizer.urls")),
    path("__debug__/", include(debug_toolbar.urls)),
    path("test/", lambda request: render(request, "test.html")),
    path("", lambda request: render(request, "home.html")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

import debug_toolbar
from django.contrib import admin
from django.urls import include, path

from seminare.problemy import views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", views.home, name="home"),
    path("problems/", views.problem_list, name="main"),
    path("problem/<id>/", views.problem_detail, name="detail"),
    path("problem/<id>/submit/", views.problem_submit, name="submit"),
    path("__debug__/", include(debug_toolbar.urls)),
]

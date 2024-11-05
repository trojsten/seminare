from django.contrib import admin
from django.urls import path

from seminare.style import views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", views.problem_list),
    path("problem/<id>/", views.problem_detail),
]

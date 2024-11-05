from django.contrib import admin
from django.urls import path

from seminare.problemy import views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", views.problem_list, name="main"),
    path("problem/<id>/", views.problem_detail, name="detail"),
]

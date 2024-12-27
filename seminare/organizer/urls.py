from django.urls import path

from seminare.organizer.views import organizer_demo

urlpatterns = [
    path("", organizer_demo),
]

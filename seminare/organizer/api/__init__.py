from django.urls import path
from rest_framework.routers import DefaultRouter

from seminare.organizer.api.files import FileAPIView
from seminare.organizer.api.problem import ProblemViewSet
from seminare.organizer.api.problemset import ProblemSetViewSet
from seminare.organizer.api.text import TextViewSet

router = DefaultRouter()
router.register("problemsets", ProblemSetViewSet, basename="problemset")
router.register(
    r"problemsets/(?P<problemset>[^/.]+)/problems",
    ProblemViewSet,
    basename="problem",
)
router.register(
    r"problemsets/(?P<problemset>[^/.]+)/problems/(?P<problem>[^/.]+)/texts",
    TextViewSet,
    basename="text",
)

urlpatterns = [
    path("files/", FileAPIView.as_view()),
    path("files/<path:path>", FileAPIView.as_view()),
] + router.urls

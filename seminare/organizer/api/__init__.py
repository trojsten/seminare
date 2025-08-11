from rest_framework.routers import DefaultRouter

from seminare.organizer.api.problem import ProblemViewSet, TextViewSet
from seminare.organizer.api.problemset import ProblemSetViewSet

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

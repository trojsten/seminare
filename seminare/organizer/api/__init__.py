from rest_framework.routers import DefaultRouter

from seminare.organizer.api.problemset import ProblemSetViewSet

router = DefaultRouter()
router.register("problemsets", ProblemSetViewSet, basename="problemset")

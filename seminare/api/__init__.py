from django.urls import path
from rest_framework.routers import DefaultRouter

from seminare.api.external_submit import (
    ExternalSubmitAPISubmitViewSet,
    ExternalSubmitAPITokenExchangeView,
)
from seminare.api.files import FileAPIView
from seminare.api.problem import ProblemViewSet
from seminare.api.problemset import ProblemSetViewSet
from seminare.api.text import TextViewSet
from seminare.api.users import UserPushAPIView

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
router.register(
    "external-submit/submits",
    ExternalSubmitAPISubmitViewSet,
    basename="externalsubmits",
)

urlpatterns = [
    path("users/push/", UserPushAPIView.as_view()),
    path(
        "external-submit/exchange/<token>/",
        ExternalSubmitAPITokenExchangeView.as_view(),
    ),
    path("files/", FileAPIView.as_view()),
    path("files/<path:path>", FileAPIView.as_view()),
] + router.urls

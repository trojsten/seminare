from django.urls import path

from seminare.problems.views import ProblemDetailView, ProblemSetDetailView

urlpatterns = [
    path("set/<int:pk>", ProblemSetDetailView.as_view(), name="problem_set_detail"),
    path(
        "sets/<int:problem_set_id>/problem/<int:number>/",
        ProblemDetailView.as_view(),
        name="problem_detail",
    ),
]

from django.urls import path

from .views import (
    ProblemDetailView,
    ProblemSetDetailView,
    ProblemSetListView,
    ProblemSetResultsView,
)

urlpatterns = [
    path("kola/", ProblemSetListView.as_view(), name="problem_set_list"),
    path("kola/<slug>/", ProblemSetDetailView.as_view(), name="problem_set_detail"),
    path(
        "kola/<problem_set_slug>/ulohy/<int:number>/",
        ProblemDetailView.as_view(),
        name="problem_detail",
    ),
    path(
        "kola/<slug>/vysledky/",
        ProblemSetResultsView.as_view(),
        name="problem_set_results",
    ),
    path(
        "kola/<slug>/vysledky/<slug:table>/",
        ProblemSetResultsView.as_view(),
        name="problem_set_results",
    ),
]

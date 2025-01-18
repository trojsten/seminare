from django.urls import include, path

from seminare.organizer.views import grading, problem, problemset

app_name = "org"

contest_patterns = [
    path("sets/", problemset.ProblemSetListView.as_view(), name="problemset_list"),
    path(
        "sets/create/",
        problemset.ProblemSetCreateView.as_view(),
        name="problemset_create",
    ),
    path(
        "sets/<int:pk>/",
        problemset.ProblemSetUpdateView.as_view(),
        name="problemset_update",
    ),
    path(
        "grading/problem/<int:problem_id>/",
        grading.GradingOverviewView.as_view(),
        name="grading_overview",
    ),
    path(
        "grading/submit/<submit_id:submit_id>/",
        grading.GradingSubmitView.as_view(),
        name="grading_submit",
    ),
    path(
        "sets/<int:problem_set_id>/problems/",
        problem.ProblemListView.as_view(),
        name="problem_list",
    ),
]


urlpatterns = [
    path("contests/<int:contest_id>/", include(contest_patterns)),
]

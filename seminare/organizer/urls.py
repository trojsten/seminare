from django.urls import include, path

from seminare.organizer.views import problemset

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
]


urlpatterns = [
    path("contests/<int:contest_id>/", include(contest_patterns)),
]

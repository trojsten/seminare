from django.urls import include, path

from seminare.organizer.views import problemset

contest_patterns = [
    path("sets/", problemset.ProblemSetListView.as_view(), name="problemset_list"),
]


urlpatterns = [
    path("contests/<int:contest_id>/", include(contest_patterns)),
]

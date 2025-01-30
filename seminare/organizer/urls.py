from django.urls import include, path

from seminare.organizer.views import dashboard, grading, page, problem, problemset, post

app_name = "org"

contest_patterns = [
    path("", dashboard.ContestDashboardView.as_view(), name="contest_dashboard"),
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
    path(
        "sets/<int:problem_set_id>/problems/<int:problem_id>",
        problem.ProblemUpdateView.as_view(),
        name="problem_update",
    ),
    path(
        "sets/<int:problem_set_id>/problems/create/",
        problem.ProblemCreateView.as_view(),
        name="problem_create",
    ),
    path("posts/", post.PostListView.as_view(), name="post_list"),
    path("posts/<int:pk>/", post.PostUpdateView.as_view(), name="post_update"),
    path("posts/<int:pk>/delete/", post.PostDeleteView.as_view(), name="post_delete"),
    path("posts/create/", post.PostCreateView.as_view(), name="post_create"),
]


urlpatterns = [
    path("", dashboard.ContestSwitchView.as_view(), name="home"),
    path("contests/<int:contest_id>/", include(contest_patterns)),
    path("pages/", page.PageListView.as_view(), name="page_list"),
    path("pages/<int:pk>/", page.PageUpdateView.as_view(), name="page_update"),
    path("pages/<int:pk>/delete/", page.PageDeleteView.as_view(), name="page_delete"),
    path("pages/create/", page.PageCreateView.as_view(), name="page_create"),
]

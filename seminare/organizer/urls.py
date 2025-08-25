from django.urls import include, path

from seminare.organizer.views import dashboard, grading, page, post, problem, problemset

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
        "sets/<slug>/",
        problemset.ProblemSetUpdateView.as_view(),
        name="problemset_update",
    ),
    path(
        "grading/problem/<int:problem_id>/",
        grading.GradingOverviewView.as_view(),
        name="grading_overview",
    ),
    path(
        "grading/problem/<int:problem_id>/bulk/",
        grading.BulkGradingView.as_view(),
        name="bulk_grading",
    ),
    path(
        "grading/problem/<int:problem_id>/bulk/download/",
        grading.BulkGradingDownloadView.as_view(),
        name="bulk_grading_download",
    ),
    path(
        "grading/submit/<submit_id:submit_id>/",
        grading.GradingSubmitView.as_view(),
        name="grading_submit",
    ),
    path(
        "sets/<problem_set_slug>/problems/",
        problem.ProblemListView.as_view(),
        name="problem_list",
    ),
    path(
        "sets/<problem_set_slug>/problems/<int:problem_id>/",
        problem.ProblemUpdateView.as_view(),
        name="problem_update",
    ),
    path(
        "sets/<problem_set_slug>/problems/create/",
        problem.ProblemCreateView.as_view(),
        name="problem_create",
    ),
    path("posts/", post.PostListView.as_view(), name="post_list"),
    path("posts/<int:pk>/", post.PostUpdateView.as_view(), name="post_update"),
    path("posts/<int:pk>/delete/", post.PostDeleteView.as_view(), name="post_delete"),
    path("posts/create/", post.PostCreateView.as_view(), name="post_create"),
]


urlpatterns = [
    path("contests/", include(contest_patterns)),
    path("pages/", page.PageListView.as_view(), name="page_list"),
    path("pages/<int:pk>/", page.PageUpdateView.as_view(), name="page_update"),
    path("pages/<int:pk>/delete/", page.PageDeleteView.as_view(), name="page_delete"),
    path("pages/create/", page.PageCreateView.as_view(), name="page_create"),
    path(
        "pages/create/<path:slug>/", page.PageCreateView.as_view(), name="page_create"
    ),
]

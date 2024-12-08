from django.urls import path

from .views import (
    FileSubmitDetailView,
    JudgeSubmitDetailView,
    SubmitListView,
    TextSubmitDetailView,
    file_submit_create_view,
)

urlpatterns = [
    path("<int:problem_id>", SubmitListView.as_view(), name="problem_submit_list"),
    path(
        "file_submit/<int:pk>",
        FileSubmitDetailView.as_view(),
        name="file_submit_detail",
    ),
    path(
        "judge_submit/<int:pk>",
        JudgeSubmitDetailView.as_view(),
        name="judge_submit_detail",
    ),
    path(
        "text_submit/<int:pk>",
        TextSubmitDetailView.as_view(),
        name="text_submit_detail",
    ),
    path(
        "file_submit/create/<int:problem>", file_submit_create_view, name="file_submit"
    ),
]

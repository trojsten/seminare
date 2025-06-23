from django.urls import path

from .views import (
    FileSubmitCreateView,
    JudgeReportView,
    JudgeSubmitCreateView,
    SubmitDetailView,
    TextSubmitCreateView,
)

urlpatterns = [
    path(
        "submits/<submit_id:submit_id>/",
        SubmitDetailView.as_view(),
        name="submit_detail",
    ),
    path(
        "submit/create/file/<int:problem>",
        FileSubmitCreateView.as_view(),
        name="file_submit",
    ),
    path(
        "submit/create/judge/<int:problem>",
        JudgeSubmitCreateView.as_view(),
        name="judge_submit",
    ),
    path(
        "submit/create/text/<int:problem>",
        TextSubmitCreateView.as_view(),
        name="text_submit",
    ),
    path(
        "submit/report/judge/",
        JudgeReportView.as_view(),
        name="judge_report",
    ),
]

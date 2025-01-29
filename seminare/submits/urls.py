from django.urls import path

from .views import (
    SubmitDetailView,
    file_submit_create_view,
)

urlpatterns = [
    path(
        "submits/<submit_id:submit_id>/",
        SubmitDetailView.as_view(),
        name="submit_detail",
    ),
    path(
        "file_submit/create/<int:problem>", file_submit_create_view, name="file_submit"
    ),
]

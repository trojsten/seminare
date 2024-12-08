from django.urls import path

from .views import ProblemDetailView, ProblemSetDetailView, ProblemSetListView

urlpatterns = [
    path("sets/", ProblemSetListView.as_view(), name="problem_set_list"),
    path("sets/<int:pk>/", ProblemSetDetailView.as_view(), name="problem_set_detail"),
    path(
        "sets/<int:problem_set_id>/problems/<int:number>/",
        ProblemDetailView.as_view(),
        name="problem_detail",
    ),
]

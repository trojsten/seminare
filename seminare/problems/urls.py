from django.urls import path

from .views import ProblemDetailView, ProblemSetDetailView, ProblemSetListView

urlpatterns = [
    path("<int:pk>", ProblemDetailView.as_view(), name="problem_detail"),
    path("set/", ProblemSetListView.as_view(), name="problem_set_list"),
    path("set/<int:pk>", ProblemSetDetailView.as_view(), name="problem_set_detail"),
]

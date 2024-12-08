from django.urls import path

from .views import ProblemSetDetailView, ProblemDetailView

urlpatterns = [
    path("<int:pk>", ProblemDetailView.as_view(), name="problem_detail"),
    path("set/<int:pk>", ProblemSetDetailView.as_view(), name="problem_set_detail"),
]

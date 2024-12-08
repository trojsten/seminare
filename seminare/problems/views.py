from django.utils import timezone
from django.views.generic import DetailView

from seminare.problems.models import ProblemSet, Problem


class ProblemDetailView(DetailView):
    queryset = Problem.objects.get_queryset()
    template_name = "problem_detail.html"
    context_object_name = "problem"


class ProblemSetDetailView(DetailView):
    queryset = ProblemSet.objects.get_queryset()
    template_name = "problem_set_detail.html"
    context_object_name = "problem_set"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        problem_set: ProblemSet = ctx["problem_set"]
        total_length_days = (problem_set.end_date - problem_set.start_date).days
        elapsed_length_days = (timezone.now().date() - problem_set.start_date).days
        ctx["progress"] = int(elapsed_length_days / total_length_days * 100)
        return ctx

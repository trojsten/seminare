from django.contrib.sites.shortcuts import get_current_site
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.views.generic import DetailView

from seminare.problems.models import Problem, ProblemSet, Text


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


class ProblemDetailView(DetailView):
    template_name = "problems/detail.html"

    def get_object(self, queryset=None):
        site = get_current_site(self.request)
        return get_object_or_404(
            Problem,
            number=self.kwargs["number"],
            problem_set_id=self.kwargs["problem_set_id"],
            problem_set__contest__site=site,
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        self.object: Problem
        ctx["statement"] = self.object.text_set.filter(
            type=Text.Type.PROBLEM_STATEMENT
        ).first()
        ctx["problems"] = Problem.objects.filter(
            problem_set_id=self.kwargs["problem_set_id"]
        )
        return ctx

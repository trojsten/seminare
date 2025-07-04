from django.contrib.sites.shortcuts import get_current_site
from django.shortcuts import get_object_or_404
from django.views.generic import DetailView, ListView

from seminare.problems.logic import inject_user_score
from seminare.problems.models import Problem, ProblemSet
from seminare.submits.models import FileSubmit, JudgeSubmit, TextSubmit


class ProblemSetListView(ListView):
    template_name = "sets/list.html"

    def get_queryset(self):
        site = get_current_site(self.request)
        return ProblemSet.objects.for_user(self.request.user).filter(contest__site=site)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)

        current_sets = ProblemSet.objects.for_user(self.request.user).only_current()
        for pset in current_sets:
            pset.problems_with_score = inject_user_score(
                pset.problems.all(), self.request.user
            )

        ctx["current_sets"] = current_sets
        return ctx


class ProblemSetDetailView(DetailView):
    queryset = ProblemSet.objects.get_queryset()
    template_name = "sets/detail.html"

    def get_queryset(self):
        site = get_current_site(self.request)
        return ProblemSet.objects.for_user(self.request.user).filter(contest__site=site)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["problems"] = inject_user_score(
            self.object.problems.all(), self.request.user
        )
        return ctx


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

    def get_submits(self):
        if not self.request.user.is_authenticated:
            return {}

        return {
            "file": FileSubmit.objects.filter(
                enrollment__user=self.request.user, problem=self.object
            ),
            "judge": JudgeSubmit.objects.filter(
                enrollment__user=self.request.user, problem=self.object
            ),
            "text": TextSubmit.objects.filter(
                enrollment__user=self.request.user, problem=self.object
            ),
        }

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        self.object: Problem
        ctx["texts"] = self.object.get_texts()
        ctx["sidebar_problems"] = inject_user_score(
            Problem.objects.filter(problem_set_id=self.kwargs["problem_set_id"]),
            self.request.user,
        )
        ctx["submits"] = self.get_submits()
        return ctx

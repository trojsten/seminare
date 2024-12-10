from django.contrib.auth.models import AnonymousUser
from django.contrib.sites.shortcuts import get_current_site
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.views.generic import DetailView, ListView

from seminare.problems.models import Problem, ProblemSet
from seminare.submits.models import FileSubmit, JudgeSubmit, TextSubmit


class ProblemSetListView(ListView):
    queryset = ProblemSet.objects.get_queryset().filter(end_date__lt=timezone.now())
    template_name = "problem_set_list.html"
    context_object_name = "problem_sets"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)

        in_progress_problem_sets = ProblemSet.objects.all().filter(
            end_date__gte=timezone.now()
        )
        ctx["problem_set_details"] = [
            ProblemSetDetailView.get_problem_set_context(problem_set, self.request.user)
            for problem_set in in_progress_problem_sets
        ]
        return ctx


class ProblemSetDetailView(DetailView):
    queryset = ProblemSet.objects.get_queryset()
    template_name = "problem_set_detail.html"
    context_object_name = "problem_set"

    @staticmethod
    def get_problem_set_context(problem_set: ProblemSet, user):
        ctx = {"problem_set": problem_set}
        total_length_days = (problem_set.end_date - problem_set.start_date).days
        elapsed_length_days = (timezone.now().date() - problem_set.start_date).days
        ctx["progress"] = int(elapsed_length_days / total_length_days * 100)

        if isinstance(user, AnonymousUser):
            return ctx

        ctx["submits"] = dict()
        ctx["submitted"] = dict()
        for problem in problem_set.problems.all():
            points = None
            file = (
                FileSubmit.objects.filter(enrollment__user=user, problem=problem)
                .order_by("-score")
                .first()
            )
            if file is not None:
                if file.score is None:
                    points = "?"
                elif points is None:
                    points = file.score
                else:
                    points += file.score

            text = (
                TextSubmit.objects.filter(enrollment__user=user, problem=problem)
                .order_by("-score")
                .first()
            )
            if text is not None:
                if text.score is None:
                    points = "?"
                elif points is None:
                    points = text.score
                else:
                    points += text.score

            judge = (
                JudgeSubmit.objects.filter(enrollment__user=user, problem=problem)
                .order_by("-score")
                .first()
            )
            if judge is not None:
                if judge.score is None:
                    points = "?"
                elif points is None:
                    points = judge.score
                else:
                    points += judge.score

            ctx["submits"][problem.id] = points

        return ctx

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        return ctx | self.get_problem_set_context(ctx["problem_set"], self.request.user)


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
            )
        }

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        self.object: Problem
        ctx["texts"] = self.object.get_texts()
        ctx["problems"] = Problem.objects.filter(
            problem_set_id=self.kwargs["problem_set_id"]
        )
        ctx["submits"] = self.get_submits()
        return ctx

from django.contrib.auth.models import AnonymousUser
from django.db.models import Max, Q
from django.utils import timezone
from django.views.generic import DetailView, ListView

from seminare.problems.models import Problem, ProblemSet
from seminare.submits.models import FileSubmit, JudgeSubmit, TextSubmit


class ProblemDetailView(DetailView):
    queryset = Problem.objects.get_queryset()
    template_name = "problem_detail.html"
    context_object_name = "problem"


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
        for problem in problem_set.problems.all():
            ctx["submits"][problem.pk] = 0
            ctx["submits"][problem.pk] += (
                FileSubmit.objects.all()
                .filter(Q(enrollment__user=user) & Q(problem=problem))
                .aggregate(Max("score", default=0))
            )["score__max"]
            ctx["submits"][problem.pk] += (
                TextSubmit.objects.all()
                .filter(Q(enrollment__user=user) & Q(problem=problem))
                .aggregate(Max("score", default=0))
            )["score__max"]
            ctx["submits"][problem.pk] += (
                JudgeSubmit.objects.all()
                .filter(Q(enrollment__user=user) & Q(problem=problem))
                .aggregate(Max("score", default=0))
            )["score__max"]
        return ctx

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        return ctx | self.get_problem_set_context(ctx["problem_set"], self.request.user)

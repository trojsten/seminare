from django.contrib.auth.models import AnonymousUser
from django.db.models import Max, Q
from django.utils import timezone
from django.views.generic import DetailView

from seminare.problems.models import Problem, ProblemSet
from seminare.submits.models import FileSubmit, JudgeSubmit, TextSubmit


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

        if isinstance(self.request.user, AnonymousUser):
            return ctx

        ctx["submits"] = dict()
        for problem in problem_set.problems.all():
            ctx["submits"][problem.pk] = 0
            ctx["submits"][problem.pk] += (
                FileSubmit.objects.all()
                .filter(Q(enrollment__user=self.request.user) & Q(problem=problem))
                .aggregate(Max("score", default=0))
            )["score__max"]
            ctx["submits"][problem.pk] += (
                TextSubmit.objects.all()
                .filter(Q(enrollment__user=self.request.user) & Q(problem=problem))
                .aggregate(Max("score", default=0))
            )["score__max"]
            ctx["submits"][problem.pk] += (
                JudgeSubmit.objects.all()
                .filter(Q(enrollment__user=self.request.user) & Q(problem=problem))
                .aggregate(Max("score", default=0))
            )["score__max"]

        return ctx

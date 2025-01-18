from django.db.models import QuerySet
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.views.generic import UpdateView

from seminare.organizer.forms import ProblemForm
from seminare.organizer.tables import ProblemTable
from seminare.organizer.views import WithContest, WithProblemSet
from seminare.organizer.views.generic import GenericFormView, GenericTableView
from seminare.problems.models import Problem


class ProblemListView(WithContest, WithProblemSet, GenericTableView):
    # TODO: Permission checking
    table_class = ProblemTable
    table_title = "Úlohy"

    def get_queryset(self) -> QuerySet[Problem]:
        return Problem.objects.filter(problem_set=self.problem_set).order_by("number")

    def get_table_links(self):
        return [
            (
                "green",
                "mdi:plus",
                "Pridať",
                reverse(
                    "org:problem_create", args=[self.contest.id, self.problem_set.id]
                ),
            )
        ]


class ProblemCreateView(WithContest, WithProblemSet, GenericFormView):
    # TODO: Permission checking
    # TODO: return to correct success url or rethink the organization
    # TODO: add texts to form aswell

    form_class = ProblemForm
    form_title = "Nová úloha"

    def form_valid(self, form):
        self.object: Problem = form.save(commit=False)
        self.object.problem_set = self.problem_set
        self.object.save()
        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self) -> str:
        return reverse("org:problem_list", args=[self.contest.id, self.problem_set.id])


class ProblemUpdateView(WithContest, WithProblemSet, GenericFormView, UpdateView):
    # TODO: Permission checking
    # TODO: return to correct success url or rethink the organization
    # TODO: add texts to form aswell
    form_class = ProblemForm
    form_title = "Upraviť úlohu"

    def get_object(self, queryset=None):
        return get_object_or_404(Problem, id=self.kwargs.get("problem_id"))

    def get_success_url(self) -> str:
        return reverse("org:problem_list", args=[self.contest.id, self.problem_set.id])

from django.db.models import QuerySet
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.views.generic import CreateView, UpdateView

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

    def get_breadcrumbs(self):
        return [
            ("Sady úloh", reverse("org:problemset_list", args=[self.contest.id])),
            (self.problem_set, ""),
            ("Úlohy", ""),
        ]

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


class ProblemCreateView(WithContest, WithProblemSet, GenericFormView, CreateView):
    # TODO: Permission checking

    form_class = ProblemForm
    form_title = "Nová úloha"

    def get_form_kwargs(self):
        kw = super().get_form_kwargs()
        kw["problem_set"] = self.problem_set
        return kw

    def get_success_url(self) -> str:
        return reverse("org:problem_list", args=[self.contest.id, self.problem_set.id])

    def get_breadcrumbs(self):
        return [
            ("Sady úloh", reverse("org:problemset_list", args=[self.contest.id])),
            (self.problem_set, ""),
            (
                "Úlohy",
                reverse(
                    "org:problem_list", args=[self.contest.id, self.problem_set.id]
                ),
            ),
            ("Nová", ""),
        ]


class ProblemUpdateView(WithContest, WithProblemSet, GenericFormView, UpdateView):
    # TODO: Permission checking

    form_class = ProblemForm
    form_title = "Upraviť úlohu"

    def get_form_kwargs(self):
        kw = super().get_form_kwargs()
        kw["problem_set"] = self.problem_set
        return kw

    def get_object(self, queryset=None):
        return get_object_or_404(Problem, id=self.kwargs.get("problem_id"))

    def get_success_url(self) -> str:
        return reverse("org:problem_list", args=[self.contest.id, self.problem_set.id])

    def get_breadcrumbs(self):
        return [
            ("Sady úloh", reverse("org:problemset_list", args=[self.contest.id])),
            (self.problem_set, ""),
            (
                "Úlohy",
                reverse(
                    "org:problem_list", args=[self.contest.id, self.problem_set.id]
                ),
            ),
            (self.object, ""),
            ("Upraviť", ""),
        ]

from django.db.models import QuerySet
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.views.generic import CreateView, UpdateView

from seminare.organizer.forms import ProblemSetForm
from seminare.organizer.tables import ProblemSetTable, ProblemTable
from seminare.organizer.views import WithContest
from seminare.organizer.views.generic import (
    GenericFormTableView,
    GenericFormView,
    GenericTableView,
)
from seminare.problems.models import Problem, ProblemSet


class ProblemSetListView(WithContest, GenericTableView):
    # TODO: Permission checking

    table_class = ProblemSetTable
    table_title = "Sady úloh"

    def get_queryset(self) -> QuerySet[ProblemSet]:
        return ProblemSet.objects.filter(contest=self.contest).order_by(
            "-end_date", "-start_date"
        )

    def get_breadcrumbs(self):
        return [("Sady úloh", "")]

    def get_table_links(self):
        return [
            (
                "green",
                "mdi:plus",
                "Pridať",
                reverse("org:problemset_create", args=[self.contest.id]),
            )
        ]


class ProblemSetCreateView(WithContest, GenericFormView, CreateView):
    # TODO: Permission checking

    form_class = ProblemSetForm
    form_title = "Nová sada úloh"

    def get_breadcrumbs(self):
        return [
            ("Sady úloh", reverse("org:problemset_list", args=[self.contest.id])),
            ("Nová sada úloh", ""),
        ]

    def form_valid(self, form):
        self.object: ProblemSet = form.save(commit=False)
        self.object.contest = self.contest
        self.object.save()
        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self) -> str:
        return reverse("problemset_list", args=[self.contest.id])


class ProblemSetUpdateView(WithContest, GenericFormTableView, UpdateView):
    # TODO: Permission checking

    form_class = ProblemSetForm
    table_class = ProblemTable
    form_table_title = "Upraviť sadu úloh"

    def get_breadcrumbs(self):
        return [
            ("Sady úloh", reverse("org:problemset_list", args=[self.contest.id])),
            (self.object, ""),
            ("Upraviť", ""),
        ]

    def get_object(self, queryset=None):
        return get_object_or_404(ProblemSet, id=self.kwargs["pk"], contest=self.contest)

    def get_queryset(self) -> QuerySet[Problem]:
        return Problem.objects.filter(problem_set=self.get_object()).order_by("number")

    def get_success_url(self) -> str:
        return reverse("problemset_list", args=[self.contest.id])

    def get_form_table_links(self):
        return [
            (
                "green",
                "mdi:plus",
                "Pridať úlohu",
                reverse(
                    "org:problem_create", args=[self.contest.id, self.get_object().id]
                ),
            ),
            (
                "default",
                "mdi:eye",
                "Pozrieť na stránke",
                reverse("problem_set_detail", args=[self.get_object().id]),
            ),
        ]

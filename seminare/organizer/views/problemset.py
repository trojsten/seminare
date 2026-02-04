from django.db.models import QuerySet
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.views.generic import CreateView, UpdateView

from seminare.organizer.forms import ProblemSetForm
from seminare.organizer.tables import ProblemSetTable, ProblemTable
from seminare.organizer.views import WithContest, WithProblemSet
from seminare.organizer.views.generic import (
    GenericFormTableView,
    GenericFormView,
    GenericTableView,
)
from seminare.problems.models import Problem, ProblemSet
from seminare.users.logic.permissions import is_contest_administrator
from seminare.users.mixins.permissions import (
    ContestAdminRequired,
    ContestOrganizerRequired,
)


class ProblemSetListView(ContestOrganizerRequired, WithContest, GenericTableView):
    table_class = ProblemSetTable
    table_title = "Sady úloh"

    def get_queryset(self) -> QuerySet[ProblemSet]:
        return ProblemSet.objects.filter(contest=self.contest).order_by(
            "-end_date", "-start_date"
        )

    def get_breadcrumbs(self):
        return [("Sady úloh", "")]

    def get_table_links(self):
        if not is_contest_administrator(self.request.user, self.contest):
            return []

        return [
            (
                "green",
                "mdi:plus",
                "Pridať",
                reverse("org:problemset_create"),
            )
        ]

    def get_table_context(self):
        return {
            "is_contest_administrator": is_contest_administrator(
                self.request.user, self.contest
            ),
        }


class ProblemSetCreateView(
    ContestAdminRequired, WithContest, GenericFormView, CreateView
):
    form_class = ProblemSetForm
    form_title = "Nová sada úloh"
    form_multipart = True

    def get_breadcrumbs(self):
        return [
            ("Sady úloh", reverse("org:problemset_list")),
            ("Nová sada úloh", ""),
        ]

    def form_valid(self, form):
        self.object: ProblemSet = form.save(commit=False)
        self.object.contest = self.contest
        self.object.save()
        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self) -> str:
        return reverse("problem_set_list")


class ProblemSetUpdateView(
    ContestAdminRequired, WithProblemSet, GenericFormTableView, UpdateView
):
    form_class = ProblemSetForm
    table_class = ProblemTable
    form_table_title = "Upraviť sadu úloh"
    form_multipart = True

    def get_breadcrumbs(self):
        return [
            ("Sady úloh", reverse("org:problemset_list")),
            (self.object, ""),
            ("Upraviť", ""),
        ]

    def get_object(self, queryset=None):
        return self.problem_set

    def get_queryset(self) -> QuerySet[Problem]:
        return Problem.objects.filter(problem_set=self.get_object()).order_by("number")

    def get_success_url(self) -> str:
        return reverse("org:problemset_list")

    def get_form_table_links(self):
        return [
            (
                "green",
                "mdi:plus",
                "Pridať úlohu",
                reverse("org:problem_create", args=[self.object.slug]),
            )
        ]

    def get_context_data(self, **kwargs):
        self.object_list = self.get_queryset()
        return super().get_context_data(**kwargs)

    def get_form_table_context(self):
        return {
            "is_contest_administrator": is_contest_administrator(
                self.request.user, self.contest
            ),
        }

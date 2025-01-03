from django.db.models import QuerySet
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.views.generic import CreateView, UpdateView

from seminare.organizer.forms import ProblemSetForm
from seminare.organizer.tables import ProblemSetTable
from seminare.organizer.views import WithContest
from seminare.organizer.views.generic import GenericFormView, GenericTableView
from seminare.problems.models import ProblemSet


class ProblemSetListView(WithContest, GenericTableView):
    # TODO: Permission checking

    table_class = ProblemSetTable
    table_title = "Sady úloh"

    def get_queryset(self) -> QuerySet[ProblemSet]:
        return ProblemSet.objects.filter(contest=self.contest).order_by(
            "-end_date", "-start_date"
        )

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

    def form_valid(self, form):
        self.object: ProblemSet = form.save(commit=False)
        self.object.contest = self.contest
        self.object.save()
        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self) -> str:
        return reverse("problemset_list", args=[self.contest.id])


class ProblemSetUpdateView(WithContest, GenericFormView, UpdateView):
    # TODO: Permission checking

    form_class = ProblemSetForm
    form_title = "Upraviť sadu úloh"

    def get_object(self, queryset=None):
        return get_object_or_404(ProblemSet, id=self.kwargs["pk"], contest=self.contest)

    def get_success_url(self) -> str:
        return reverse("problemset_list", args=[self.contest.id])

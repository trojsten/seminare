import csv
from functools import cached_property
from io import StringIO

from django.db.models import QuerySet
from django.http import HttpResponse, HttpResponseRedirect
from django.urls import reverse
from django.views.generic import CreateView, UpdateView

from seminare.organizer.forms import ProblemSetCSVExportForm, ProblemSetForm
from seminare.organizer.tables import ProblemSetTable, ProblemTable
from seminare.organizer.views import WithContest, WithProblemSet
from seminare.organizer.views.generic import (
    GenericFormTableView,
    GenericFormView,
    GenericTableView,
)
from seminare.problems.models import Problem, ProblemSet
from seminare.problems.notifications import notify_problem_set_published
from seminare.rules import RuleEngine
from seminare.users.logic.permissions import is_contest_administrator
from seminare.users.mixins.permissions import (
    ContestAdminRequired,
    ContestOrganizerRequired,
)
from seminare.users.models import User


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

        if self.object.is_public:
            notify_problem_set_published(self.object)

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

    def form_valid(self, form):
        published = "is_public" in form.changed_data and form.cleaned_data["is_public"]

        response = super().form_valid(form)

        if published:
            notify_problem_set_published(self.object)

        return response

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


class ProblemSetCSVExportView(ContestAdminRequired, WithProblemSet, GenericFormView):
    form_class = ProblemSetCSVExportForm
    form_title = "Export výsledkovky"
    form_submit_label = "Exportovať"
    form_multipart = True

    @cached_property
    def rule_engine(self) -> RuleEngine:
        return self.problem_set.get_rule_engine()

    def get_form_message(self):
        if not self.problem_set.is_finalized:
            return (
                "Výsledky tejto sady úloh ešte nie sú finalizované. Export môže obsahovať neúplné údaje.",
                "warning",
                "mdi:warning",
            )

        return super().get_form_message()

    def get_breadcrumbs(self):
        return [
            ("Sady úloh", reverse("org:problemset_list")),
            (self.problem_set, ""),
            ("CSV Export", ""),
        ]

    def get_form_kwargs(self):
        kw = super().get_form_kwargs()
        kw["rule_engine"] = self.rule_engine
        return kw

    def form_valid(self, form):
        response = HttpResponse()
        response["Content-Type"] = "text/csv"
        response["Content-Disposition"] = (
            f'attachment; filename="{self.problem_set.contest.short_name}-{self.problem_set.slug}.csv"'
        )
        csv_buffer = StringIO()
        w = csv.writer(csv_buffer)

        table_data = self.rule_engine.get_result_table(
            form.cleaned_data["result_table"]
        )

        user_ids = [
            row.enrollment.user_id
            for row in table_data.rows
            if not row.ghost or form.cleaned_data["include_ghost"]
        ]
        user_trojsten_ids = User.objects.filter(id__in=user_ids).values_list(
            "id", "trojsten_id"
        )
        user_trojsten_ids = dict(user_trojsten_ids)

        w.writerow(
            ["Poradie", "Meno", "Email", "Trojsten ID", "Škola", "Ročník"]
            + [c.export() for c in table_data.columns]
            + ["Body spolu"]
        )
        curr_rank = None
        for row in table_data.rows:
            if row.ghost and not form.cleaned_data["include_ghost"]:
                continue

            if row.rank is not None:
                curr_rank = row.rank

            w.writerow(
                [
                    curr_rank,
                    row.enrollment.user.display_name,
                    row.enrollment.user.email,
                    user_trojsten_ids.get(row.enrollment.user_id, None),
                    row.enrollment.school,
                    row.enrollment.grade,
                ]
                + [col.export() if col else "" for col in row.columns]
                + [row.total]
            )

        response.write(csv_buffer.getvalue())
        return response

    def get_success_url(self) -> str:
        return reverse("org:problemset_list")

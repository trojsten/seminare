from django.contrib.auth.models import AnonymousUser
from django.contrib.sites.shortcuts import get_current_site
from django.http.response import Http404
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.views.generic import DetailView, ListView

from seminare.contests.utils import get_current_contest
from seminare.problems.logic import inject_chips, inject_user_score
from seminare.problems.models import Problem, ProblemSet
from seminare.rules import RuleEngine
from seminare.submits.models import FileSubmit, JudgeSubmit, TextSubmit
from seminare.users.logic.permissions import is_contest_organizer
from seminare.users.models import Enrollment, User


class ProblemSetListView(ListView):
    template_name = "sets/list.html"

    def get_queryset(self):
        site = get_current_site(self.request)
        return ProblemSet.objects.for_user(self.request.user).filter(contest__site=site)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)

        current_sets = ProblemSet.objects.for_user(self.request.user).only_current()
        for pset in current_sets:
            pset.problems_with_score = inject_user_score(pset, self.request.user)

        ctx["current_sets"] = current_sets
        return ctx


class ProblemSetDetailView(DetailView):
    queryset = ProblemSet.objects.get_queryset()
    template_name = "sets/detail.html"
    object: ProblemSet

    def get_queryset(self):
        site = get_current_site(self.request)
        return ProblemSet.objects.for_user(self.request.user).filter(contest__site=site)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["problems"] = inject_chips(
            inject_user_score(self.object, self.request.user),
            self.object.get_rule_engine().get_chips(self.request.user),
        )
        return ctx


class ProblemSetResultsView(DetailView):
    queryset = ProblemSet.objects.get_queryset()
    template_name = "sets/results.html"
    object: ProblemSet

    def get_queryset(self):
        site = get_current_site(self.request)
        return (
            ProblemSet.objects.for_user(self.request.user)
            .filter(contest__site=site)
            .select_related("contest")
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)

        rule_engine: RuleEngine = self.object.get_rule_engine()

        user = None
        if self.request.user.is_authenticated:
            assert isinstance(self.request.user, User)
            user = self.request.user

        result_tables = rule_engine.get_result_tables()
        selected_table: str = (
            self.kwargs["table"]
            if "table" in self.kwargs
            else rule_engine.get_default_result_table(user)
        )

        if selected_table not in result_tables:
            raise Http404("Result table not found.")

        table = rule_engine.get_result_table(selected_table)

        show_ghost = False

        if user:
            is_organizer = is_contest_organizer(user, get_current_contest(self.request))
            is_ghost = next(
                (r.ghost for r in table.rows if r.enrollment.user == user),
                None,
            )

            show_ghost = is_organizer or is_ghost

        if not show_ghost:
            table.rows = [row for row in table.rows if not row.ghost]

        ctx["table"] = table
        ctx["result_tables"] = result_tables
        ctx["selected_table"] = selected_table
        ctx["selected_table_name"] = result_tables[selected_table]

        return ctx


class ProblemDetailView(DetailView):
    template_name = "problems/detail.html"
    object: Problem

    def get_object(self, queryset=None):
        self.contest = get_current_contest(self.request)
        return get_object_or_404(
            Problem.objects.select_related("problem_set"),
            number=self.kwargs["number"],
            problem_set__slug=self.kwargs["problem_set_slug"],
            problem_set__contest=self.contest,
        )

    def get_submits(self):
        if not self.request.user.is_authenticated:
            return {}

        rule_engine: RuleEngine = self.object.problem_set.get_rule_engine()
        enrollment = Enrollment.objects.filter(
            problem_set=self.object.problem_set, user=self.request.user
        ).first()

        if enrollment is not None:
            enrollment.user = self.request.user

        return {
            id: {
                "icon": icon,
                "name": name,
                "action": reverse(f"{id}_submit", args=[self.object.id]),
                "points": getattr(self.object, f"{id}_points", 0),
                "chip": rule_engine.get_submits_chip(cls, self.object, enrollment),
                "can_submit": rule_engine.can_submit(cls, self.object, enrollment),
                "submits": cls.objects.filter(
                    enrollment=enrollment, problem=self.object
                ),
            }
            for id, cls, name, icon in (
                ("file", FileSubmit, "popis", "mdi:file-text"),
                ("judge", JudgeSubmit, "program", "mdi:file-code"),
                ("text", TextSubmit, "odpoveď", "mdi:format-text"),
            )
            if cls in self.object.accepted_submit_classes
        }

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        assert isinstance(self.request.user, User | AnonymousUser)

        chips = self.object.problem_set.get_rule_engine().get_chips(self.request.user)

        ctx["texts"] = self.object.get_all_texts()
        ctx["sidebar_problems"] = inject_chips(
            inject_user_score(
                self.object.problem_set,
                self.request.user,
            ),
            chips,
        )
        ctx["chips"] = chips[self.object]
        if isinstance(self.request.user, User):
            ctx["is_organizer"] = is_contest_organizer(self.request.user, self.contest)
        ctx["submits"] = self.get_submits()
        return ctx

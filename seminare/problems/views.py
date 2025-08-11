from django.contrib.auth.models import AnonymousUser
from django.contrib.sites.shortcuts import get_current_site
from django.http.response import Http404
from django.shortcuts import get_object_or_404
from django.views.generic import DetailView, ListView

from seminare.contests.utils import get_current_contest
from seminare.problems.logic import inject_user_score
from seminare.problems.models import Problem, ProblemSet
from seminare.rules import RuleEngine
from seminare.submits.models import FileSubmit, JudgeSubmit, TextSubmit
from seminare.users.logic.permissions import is_contest_organizer
from seminare.users.models import User


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

    def get_queryset(self):
        site = get_current_site(self.request)
        return ProblemSet.objects.for_user(self.request.user).filter(contest__site=site)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["problems"] = inject_user_score(self.object, self.request.user)
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
        site = get_current_site(self.request)
        return get_object_or_404(
            Problem.objects.select_related("problem_set"),
            number=self.kwargs["number"],
            problem_set__slug=self.kwargs["problem_set_slug"],
            problem_set__contest__site=site,
        )

    def get_submits(self):
        if not self.request.user.is_authenticated:
            return {}

        return {
            "file": FileSubmit.objects.filter(
                enrollment__user=self.request.user, problem=self.object
            ),
            "judge": JudgeSubmit.objects.filter(
                enrollment__user=self.request.user, problem=self.object
            ),
            "text": TextSubmit.objects.filter(
                enrollment__user=self.request.user, problem=self.object
            ),
        }

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        assert isinstance(self.request.user, User | AnonymousUser)

        ctx["texts"] = self.object.get_all_texts()
        ctx["sidebar_problems"] = inject_user_score(
            self.object.problem_set,
            self.request.user,
        )
        if isinstance(self.request.user, User):
            ctx["is_organizer"] = is_contest_organizer(
                self.request.user, get_current_contest(self.request)
            )
        ctx["submits"] = self.get_submits()
        return ctx

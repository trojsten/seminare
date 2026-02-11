from functools import cached_property

from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import PermissionDenied
from django.http.response import Http404
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.views.generic import DetailView, ListView, View
from django.views.generic.detail import SingleObjectMixin

from seminare.contests.utils import get_current_contest
from seminare.problems.logic import (
    inject_chips,
    inject_points_visible,
    inject_user_score,
)
from seminare.problems.models import Problem, ProblemSet, Text
from seminare.rules import RuleEngine
from seminare.submits.models import FileSubmit, JudgeSubmit, TextSubmit
from seminare.users.logic.permissions import (
    is_contest_administrator,
    is_contest_organizer,
)
from seminare.users.models import User
from seminare.utils import sendfile


class ProblemSetListView(ListView):
    template_name = "sets/list.html"

    def get_queryset(self):
        self.contest = get_current_contest(self.request)
        return ProblemSet.objects.for_user(self.request.user, self.contest).order_by(
            "-end_date", "-start_date"
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)

        current_sets = (
            ProblemSet.objects.for_user(self.request.user, self.contest)
            .only_current()
            .prefetch_related("problems")
        )

        for pset in current_sets:
            rule_engine = pset.get_rule_engine()
            pset.problems_with_score = inject_chips(
                inject_user_score(pset, self.request.user),
                rule_engine.get_chips(self.request.user),
            )
            pset.visible_pdfs = rule_engine.get_visible_texts(None)

        ctx["current_sets"] = current_sets
        return ctx


class ProblemSetDetailView(DetailView):
    queryset = ProblemSet.objects.get_queryset()
    template_name = "sets/detail.html"
    object: ProblemSet

    def get_queryset(self):
        self.contest = get_current_contest(self.request)
        return ProblemSet.objects.for_user(
            self.request.user, self.contest
        ).prefetch_related("problems")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)

        rule_engine = self.object.get_rule_engine()

        ctx["problems"] = inject_chips(
            inject_user_score(self.object, self.request.user),
            rule_engine.get_chips(self.request.user),
        )
        ctx["visible_pdfs"] = rule_engine.get_visible_texts(None)

        ctx["sets"] = ProblemSet.objects.for_user(
            self.request.user, self.contest
        ).order_by("-end_date", "-start_date")
        return ctx


class ProblemSetResultsView(DetailView):
    queryset = ProblemSet.objects.get_queryset()
    template_name = "sets/results.html"
    object: ProblemSet

    def get_queryset(self):
        contest = get_current_contest(self.request)
        return (
            ProblemSet.objects.for_user(self.request.user, contest)
            .filter(contest=contest)
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
        problem_set = get_object_or_404(
            ProblemSet.objects.for_user(self.request.user, self.contest)
            .filter(slug=self.kwargs["problem_set_slug"])
            .prefetch_related("problems")
        )
        problem_set.contest = self.contest

        problem = next(
            (
                problem
                for problem in problem_set.problems.all()
                if problem.number == self.kwargs["number"]
            ),
            None,
        )

        if problem is None:
            raise Http404()

        return problem

    @cached_property
    def rule_engine(self) -> RuleEngine:
        return self.object.problem_set.get_rule_engine()

    def get_submits(self, enrollment):
        if not self.request.user.is_authenticated:
            return {}

        return {
            id: {
                "icon": icon,
                "name": name,
                "action": reverse(f"{id}_submit", args=[self.object.id]),
                "points": getattr(self.object, f"{id}_points", 0),
                "chip": self.rule_engine.get_submits_chip(cls, self.object, enrollment),
                "can_submit": self.rule_engine.can_submit(cls, self.object, enrollment),
                "submits": inject_points_visible(
                    cls.objects.filter(enrollment=enrollment, problem=self.object),
                    self.object,
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

        enrollment = None

        if (user := self.request.user).is_authenticated:
            assert isinstance(user, User)
            enrollment = self.rule_engine.get_enrollment(user)

            if enrollment is not None:
                enrollment.user = user
                ctx["enrollment"] = enrollment

                if self.object.problem_set.is_running and (
                    enrollment.school_id != user.current_school_id
                    or enrollment.grade != user.current_grade
                ):
                    ctx["enrollment_warning"] = True

        chips = self.rule_engine.get_chips(self.request.user)

        ctx["texts"] = self.object.get_all_texts()
        ctx["sidebar_problems"] = inject_chips(
            inject_user_score(
                self.object.problem_set,
                self.request.user,
            ),
            chips,
        )
        ctx["chips"] = chips[self.object]
        ctx["links"] = []
        if isinstance(self.request.user, User):
            if is_contest_organizer(self.request.user, self.contest):
                ctx["is_organizer"] = True

                ctx["links"].append(
                    (
                        "default",
                        "mdi:comment-arrow-left",
                        "Opravovanie",
                        reverse(
                            "org:grading_overview",
                            args=[self.object.problem_set.slug, self.object.number],
                        ),
                    )
                )

            if is_contest_administrator(self.request.user, self.contest):
                ctx["links"].append(
                    (
                        "default",
                        "mdi:pencil",
                        "Upraviť úlohu",
                        reverse(
                            "org:problem_update",
                            args=[self.object.problem_set.slug, self.object.number],
                        ),
                    )
                )

        ctx["submits"] = self.get_submits(enrollment)
        return ctx


class ProblemSolutionView(ProblemDetailView):
    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["solution"] = True
        return ctx


class StatementPDFView(SingleObjectMixin, View):
    file_getter = "statement_pdf"
    file_type = Text.Type.PROBLEM_STATEMENT

    def get_queryset(self):
        contest = get_current_contest(self.request)
        return ProblemSet.objects.for_user(self.request.user, contest)

    def get(self, request, *args, **kwargs):
        problem_set: ProblemSet = self.get_object()
        visible = problem_set.get_rule_engine().get_visible_texts(None)
        if self.file_type not in visible:
            raise PermissionDenied()

        file = getattr(problem_set, self.file_getter)
        if not file:
            raise Http404()

        return sendfile(file.path)


class SolutionPDFView(StatementPDFView):
    file_getter = "solution_pdf"
    file_type = Text.Type.EXAMPLE_SOLUTION

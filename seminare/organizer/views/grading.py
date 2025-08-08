from collections import defaultdict
from typing import Iterable

from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.utils.functional import cached_property
from django.views.generic import FormView, TemplateView

from seminare.organizer.forms import GradingForm
from seminare.organizer.views import (
    MixinProtocol,
    WithBreadcrumbs,
    WithContest,
    WithSubmit,
)
from seminare.problems.models import Problem
from seminare.rules import RuleEngine
from seminare.submits.models import BaseSubmit
from seminare.users.mixins.permissions import ContestOrganizerRequired
from seminare.users.models import Enrollment


class WithSubmitList(WithContest, MixinProtocol):
    problem: Problem | cached_property

    @cached_property
    def rule_engine(self) -> RuleEngine:
        return self.problem.problem_set.get_rule_engine()

    def get_submits(
        self,
        enrollments: Iterable[Enrollment],
        limit_types: Iterable[str] | None = None,
    ) -> dict[int, dict[str, BaseSubmit | None]]:
        """
        Returns one submit of each type for every user.
        Returned as dict [user_id][submit_type]
        """
        submits_user = defaultdict(dict)

        for submit_cls in BaseSubmit.get_submit_types():
            if limit_types and submit_cls.type not in limit_types:
                continue

            submit_objs = self.rule_engine.get_enrollments_problems_effective_submits(
                submit_cls, enrollments, [self.problem]
            ).select_related("scored_by")

            for submit in submit_objs:
                submits_user[submit.enrollment_id][submit_cls.type] = submit

        return submits_user

    def get_users_with_submits(self, limit_types=None):
        data = []
        enrollments = self.rule_engine.get_enrollments().select_related("user")
        submits = self.get_submits(enrollments, limit_types)

        for enrollment in enrollments:
            row: dict = {"user": enrollment.user}
            row.update(submits[enrollment.id])
            if limit_types and len(limit_types) == 1:
                row["submit"] = submits[enrollment.id].get(limit_types[0])
            data.append(row)

        return data


class GradingOverviewView(
    ContestOrganizerRequired, WithSubmitList, WithBreadcrumbs, TemplateView
):
    template_name = "org/grading/overview.html"

    @cached_property
    def problem(self):
        return get_object_or_404(
            Problem, id=self.kwargs["problem_id"], problem_set__contest=self.contest
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["problem"] = self.problem
        ctx["users"] = self.get_users_with_submits(self.problem.accepted_submit_types)
        return ctx

    def get_breadcrumbs(self):
        return [
            ("Sady úloh", reverse("org:problemset_list")),
            (self.problem.problem_set, ""),
            (
                "Úlohy",
                reverse(
                    "org:problem_list",
                    args=[self.problem.problem_set.slug],
                ),
            ),
            (self.problem, ""),
            ("Opravovanie", ""),
        ]


class GradingSubmitView(ContestOrganizerRequired, WithSubmit, WithSubmitList, FormView):
    template_name = "org/grading/submit.html"
    form_class = GradingForm

    @cached_property
    def problem(self):
        return self.submit.problem

    def get_other_submits(self):
        submit_cls = self.submit.__class__
        submits = submit_cls.objects.filter(
            enrollment=self.submit.enrollment, problem=self.submit.problem
        )
        deadlines = self.problem.problem_set.get_rule_engine().get_important_dates()

        out = []
        for deadline, label in deadlines:
            out.append({"type": "deadline", "time": deadline, "label": label})
        for submit in submits:
            out.append(
                {
                    "type": "submit",
                    "time": submit.created_at,
                    "submit": submit,
                }
            )

        out.sort(key=lambda x: x["time"])

        return out

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["other_submits"] = self.get_other_submits()
        ctx["other_users"] = self.get_users_with_submits([self.submit.type])
        return ctx

    def get_initial(self):
        initial = super().get_initial()
        initial["score"] = self.submit.score
        initial["comment"] = self.submit.comment
        return initial

    def form_valid(self, form):
        self.submit.comment = form.cleaned_data.get("comment")
        self.submit.score = form.cleaned_data.get("score")
        self.submit.scored_by = self.request.user
        self.submit.save()
        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):
        return reverse("org:grading_submit", args=[self.submit.submit_id])

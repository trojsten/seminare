from collections import defaultdict

from django.db.models import F
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.utils.functional import cached_property
from django.views.generic import FormView, TemplateView

from seminare.organizer.forms import GradingForm
from seminare.organizer.views import MixinProtocol, WithContest, WithSubmit
from seminare.problems.models import Problem
from seminare.submits.models import BaseSubmit, FileSubmit, JudgeSubmit, TextSubmit
from seminare.users.models import User


class WithSubmitList(WithContest, MixinProtocol):
    problem: Problem | cached_property

    def get_users(self):
        return User.objects.filter(enrollment__problem_set=self.problem.problem_set)

    def get_submit_types(self) -> dict[str, type[BaseSubmit]]:
        return {"judge": JudgeSubmit, "text": TextSubmit, "file": FileSubmit}

    def get_submits(
        self, users, limit_types=None
    ) -> dict[int, dict[str, BaseSubmit | None]]:
        """
        Returns one submit of each type for every user.
        Returned as dict [user_id][submit_type]
        """
        submits_user = defaultdict(dict)

        for submit_type, submit_cls in self.get_submit_types().items():
            if limit_types and submit_type not in limit_types:
                continue
            # TODO: Last submit before round end!
            submit_objs = (
                submit_cls.objects.filter(
                    enrollment__user__in=users, problem=self.problem
                )
                .order_by(
                    "enrollment_id", F("score").desc(nulls_last=True), "-created_at"
                )
                .distinct("enrollment_id")
                .select_related("enrollment", "scored_by")
            )

            for submit in submit_objs:
                submits_user[submit.enrollment.user_id][submit_type] = submit

        return submits_user

    def get_users_with_submits(self, limit_types=None):
        data = []
        users = self.get_users()
        submits = self.get_submits(users, limit_types)

        for user in users:
            row: dict = {"user": user}
            row.update(submits[user.id])
            if limit_types and len(limit_types) == 1:
                row["submit"] = submits[user.id][limit_types[0]]
            data.append(row)

        return data


class GradingOverviewView(WithSubmitList, TemplateView):
    # TODO: Permission checking
    template_name = "org/grading/overview.html"

    @cached_property
    def problem(self):
        return get_object_or_404(
            Problem, id=self.kwargs["problem_id"], problem_set__contest=self.contest
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["problem"] = self.problem
        ctx["users"] = self.get_users_with_submits()
        return ctx


class GradingSubmitView(WithSubmit, WithSubmitList, FormView):
    # TODO: Permission checking
    template_name = "org/grading/submit.html"
    form_class = GradingForm

    @cached_property
    def problem(self):
        return self.submit.problem

    def get_other_submits(self):
        submit_cls = self.submit.__class__
        return submit_cls.objects.filter(
            enrollment=self.submit.enrollment, problem=self.submit.problem
        )

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
        return reverse(
            "org:grading_submit", args=[self.contest.id, self.submit.submit_id]
        )

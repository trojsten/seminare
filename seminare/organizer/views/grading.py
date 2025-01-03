from collections import defaultdict

from django.shortcuts import get_object_or_404
from django.utils.functional import cached_property
from django.views.generic import TemplateView

from seminare.organizer.views import WithContest
from seminare.problems.models import Problem
from seminare.submits.models import BaseSubmit, FileSubmit, JudgeSubmit, TextSubmit
from seminare.users.models import User


class GradingOverviewView(WithContest, TemplateView):
    # TODO: Permission checking
    template_name = "org/grading/overview.html"

    @cached_property
    def problem(self):
        return get_object_or_404(
            Problem, id=self.kwargs["problem_id"], problem_set__contest=self.contest
        )

    def get_users(self):
        return User.objects.filter(enrollment__problem_set=self.problem.problem_set)

    def get_submit_types(self) -> dict[str, type[BaseSubmit]]:
        return {"judge": JudgeSubmit, "text": TextSubmit, "file": FileSubmit}

    def get_submits(self, users) -> dict[int, dict[str, BaseSubmit | None]]:
        """
        Returns one submit of each type for every user.
        Returned as dict [user_id][submit_type]
        """
        submits_user = defaultdict(dict)

        for submit_type, submit_cls in self.get_submit_types().items():
            # TODO: Last submit before round end!
            submit_objs = (
                submit_cls.objects.filter(
                    enrollment__user__in=users, problem=self.problem
                )
                .order_by("enrollment_id", "-score", "-created_at")
                .distinct("enrollment_id")
                .select_related("enrollment", "scored_by")
            )

            for submit in submit_objs:
                submits_user[submit.enrollment.user_id][submit_type] = submit

        return submits_user

    def get_users_with_submits(self):
        data = []
        users = self.get_users()
        submits = self.get_submits(users)

        for user in users:
            row: dict = {"user": user}
            row.update(submits[user.id])
            data.append(row)

        return data

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["problem"] = self.problem
        ctx["users"] = self.get_users_with_submits()
        return ctx

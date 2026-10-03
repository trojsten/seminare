from django.urls import reverse

from seminare.contests.models import Contest
from seminare.problems.models import Problem, ProblemSet
from seminare.submits.models import FileSubmit
from seminare.users.logic.notifications import (
    notify,
    previous_problem_set_participants,
)
from seminare.users.models import NotificationType, User


def notify_problem_set_published(problem_set: ProblemSet) -> None:
    contest = Contest.objects.select_related("site").get(id=problem_set.contest_id)

    notify(
        previous_problem_set_participants(problem_set),
        contest,
        NotificationType.PROBLEM_SET,
        NotificationType.PROBLEM_SET.label,
        f"Bolo zverejnené nové kolo {problem_set.name}.",
        contest.absolute_url(
            reverse("problem_set_detail", args=[problem_set.slug]),
        ),
    )


def notify_problem_graded(problem: Problem) -> None:
    contest = Contest.objects.select_related("site").get(
        id=problem.problem_set.contest_id
    )

    user_ids = FileSubmit.objects.filter(
        problem=problem, score__isnull=False
    ).values_list("enrollment__user_id", flat=True)

    notify(
        User.objects.filter(id__in=user_ids).order_by("id"),
        contest,
        NotificationType.SUBMIT_GRADED,
        NotificationType.SUBMIT_GRADED.label,
        f"V úlohe {problem.name} boli zverejnené body za tvoj popis.",
        contest.absolute_url(
            reverse(
                "problem_detail",
                args=[problem.problem_set.slug, problem.number],
            ),
        ),
    )

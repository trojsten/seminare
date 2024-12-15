from collections import defaultdict
from dataclasses import dataclass
from decimal import Decimal
from typing import Iterable

from django.contrib.auth.models import AnonymousUser

from seminare.problems.models import Problem
from seminare.submits.models import BaseSubmit, FileSubmit, JudgeSubmit, TextSubmit
from seminare.users.models import User


@dataclass
class SubmitData:
    submitted: bool = False
    score: Decimal | None = None


def _get_best_submits(
    problems: Iterable[Problem], user: User, submit_cls: type[BaseSubmit]
) -> dict[int, SubmitData]:
    submits = (
        submit_cls.objects.filter(problem__in=problems, enrollment__user=user)
        .order_by("problem_id", "-score")
        .distinct("problem_id", "score")
        .values()
    )

    data = defaultdict(SubmitData)
    for submit in submits:
        data[submit["problem_id"]] = SubmitData(True, submit["score"])
    return data


def get_best_file_submits(
    problems: Iterable[Problem], user: User
) -> dict[int, SubmitData]:
    return _get_best_submits(problems, user, FileSubmit)


def get_best_judge_submits(
    problems: Iterable[Problem], user: User
) -> dict[int, SubmitData]:
    return _get_best_submits(problems, user, JudgeSubmit)


def get_best_text_submits(
    problems: Iterable[Problem], user: User
) -> dict[int, SubmitData]:
    return _get_best_submits(problems, user, TextSubmit)


def inject_user_score(
    problems: Iterable[Problem], user: User | AnonymousUser
) -> Iterable[Problem]:
    if not user.is_authenticated:
        return problems

    file_submits = get_best_file_submits(problems, user)
    judge_submits = get_best_judge_submits(problems, user)
    text_submits = get_best_text_submits(problems, user)
    submits = [file_submits, judge_submits, text_submits]

    injected = []
    for problem in problems:
        pending_submits = False
        score = None

        for submit_type in submits:
            problem_submit = submit_type[problem.id]
            if not problem_submit.submitted:
                continue

            pending_submits |= problem_submit.score is None
            if problem_submit.score is not None:
                if score is None:
                    score = problem_submit.score
                else:
                    score += problem_submit.score

        problem.users_score = score
        problem.users_score_pending = pending_submits
        injected.append(problem)

    return injected

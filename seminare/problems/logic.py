from typing import Iterable

from django.contrib.auth.models import AnonymousUser

from seminare.problems.models import Problem, ProblemSet
from seminare.rules import Chip
from seminare.users.models import User


def inject_user_score(
    problem_set: ProblemSet, user: User | AnonymousUser
) -> Iterable[Problem]:
    problems = problem_set.problems.all()

    if isinstance(user, AnonymousUser):
        return problems

    rule_engine = problem_set.get_rule_engine()

    enrollment = rule_engine.get_enrollment(user)

    if enrollment is None:
        return problems

    scores = rule_engine.get_enrollments_problems_scores([enrollment], problems)

    injected = []
    for problem in problems:
        pending_submits = False
        score = None

        if (enrollment.user_id, problem.id) in scores:
            score = scores[(enrollment.user_id, problem.id)].points
            pending_submits = scores[(enrollment.user_id, problem.id)].pending

        setattr(problem, "users_score", score)
        setattr(problem, "users_score_pending", pending_submits)
        injected.append(problem)

    return injected


def inject_chips(
    problems: Iterable[Problem], chips: dict[Problem, list[Chip]]
) -> Iterable[Problem]:
    for problem in problems:
        if problem in chips:
            setattr(problem, "chips", chips[problem])
        else:
            setattr(problem, "chips", [])
    return problems

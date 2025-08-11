from typing import Iterable

from django.contrib.auth.models import AnonymousUser

from seminare.problems.models import Problem, ProblemSet
from seminare.users.models import Enrollment, User


def inject_user_score(
    problem_set: ProblemSet, user: User | AnonymousUser
) -> Iterable[Problem]:
    problems = problem_set.problems.all()

    if isinstance(user, AnonymousUser):
        return problems

    rule_engine = problem_set.get_rule_engine()

    enrollment = Enrollment.objects.filter(user=user, problem_set=problem_set).first()

    if enrollment is None:
        return problems

    scores = rule_engine.get_enrollments_problems_scores([enrollment], problems)

    injected = []
    for problem in problems:
        pending_submits = False
        score = None

        if (enrollment.id, problem.id) in scores:
            score = scores[(enrollment.id, problem.id)].points
            pending_submits = scores[(enrollment.id, problem.id)].pending

        setattr(problem, "users_score", score)
        setattr(problem, "users_score_pending", pending_submits)
        injected.append(problem)

    return injected

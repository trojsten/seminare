from seminare.contests.models import Category
from seminare.problems.models import ProblemSet
from seminare.users.models import User, Enrollment


def get_enrollment(user: User, problem_set: ProblemSet) -> Enrollment:
    e, _ = Enrollment.objects.get_or_create(user=user, problem_set=problem_set, defaults={
        "grade": Enrollment.Grade.OLD,
        "category": Category.objects.filter(contest=problem_set.contest).first(),
    })
    return e

from seminare.problems.models import ProblemSet
from seminare.users.models import Enrollment, User


def get_enrollment(user: User, problem_set: ProblemSet) -> Enrollment:
    e, _ = Enrollment.objects.get_or_create(
        user=user,
        problem_set=problem_set,
        defaults={
            "grade": Enrollment.Grade.OLD,
        },
    )
    return e

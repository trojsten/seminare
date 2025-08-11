from seminare.problems.models import ProblemSet
from seminare.users.models import Enrollment, Grade, User


def get_enrollment(user: User, problem_set: ProblemSet) -> Enrollment:
    e, _ = Enrollment.objects.get_or_create(
        user=user,
        problem_set=problem_set,
        defaults={
            "grade": user.current_grade if user.current_grade else Grade.OLD,
            "school": user.current_school,
        },
    )
    return e

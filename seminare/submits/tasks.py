from django.urls import reverse
from django_rq import job

from seminare.contests.models import Contest
from seminare.submits.models import BaseSubmit
from seminare.users.models import User
from seminare.utils import send_mail


@job
def mail_reviewer(submit_id: str):
    submit = BaseSubmit.get_submit_by_id_queryset(submit_id)
    if submit is None:
        return

    submit = submit.select_related(
        "problem__reviewer", "problem__problem_set__contest", "enrollment__user"
    ).first()

    if submit is None or submit.problem.reviewer is None or submit.score is not None:
        return

    reviewer: User = submit.problem.reviewer
    contest: Contest = submit.problem.problem_set.contest

    send_mail(
        [reviewer.email],
        f"[{contest.short_name}] Nový submit v úlohe {submit.problem.name}",
        "reviewer_submit_notification",
        contest,
        {
            "submit": submit,
            "grade_url": f"https://{contest.site.domain}{
                reverse(
                    'org:grading_submit',
                    args=[
                        submit.problem.problem_set.slug,
                        submit.problem.number,
                        submit.submit_id,
                    ],
                )
            }",
        },
    )

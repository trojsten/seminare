from django_rq import job

from seminare.contests.models import Contest
from seminare.utils import send_mail


@job
def mail_notification(
    email: str,
    contest_id: int,
    title: str,
    content: str,
    link: str = "",
) -> None:
    contest: Contest | None = (
        Contest.objects.select_related("site").filter(id=contest_id).first()
    )
    if contest is None:
        return

    send_mail(
        [email],
        f"[{contest.short_name}] {title}",
        "notification",
        contest,
        {
            "title": title,
            "content": content,
            "link": link,
            "settings_url": contest.absolute_url("/upozornenia/"),
        },
        reply_to=[],
    )

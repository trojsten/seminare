from django_rq import job

from seminare.contests.models import Contest
from seminare.users.logic.push import send_web_push
from seminare.users.models import PushSubscription
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


@job
def push_notification(
    user_id: int,
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

    body = content if len(content) <= 240 else f"{content[:239]}…"
    payload = {
        "title": f"[{contest.short_name}] {title}",
        "body": body,
        "url": link or contest.absolute_url("/"),
    }
    for subscription in PushSubscription.objects.filter(user_id=user_id):
        send_web_push(subscription, payload)

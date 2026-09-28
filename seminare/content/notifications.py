from django.urls import reverse

from seminare.content.models import Post
from seminare.users.logic.notifications import contest_participants, notify
from seminare.users.models import NotificationType


def notify_post_published(post: Post) -> None:
    for contest in post.contests.select_related("site").all():
        notify(
            contest_participants(contest),
            contest,
            NotificationType.POST,
            NotificationType.POST.label,
            f"Bol zverejnený nový príspevok {post.title}.",
            contest.absolute_url(reverse("post_detail", args=[post.slug])),
        )

import threading
from collections.abc import Iterable
from typing import TYPE_CHECKING

from django.db.models import Q, QuerySet

from seminare.users.models import (
    Notification,
    NotificationChannel,
    NotificationPreferences,
    NotificationType,
    PushSubscription,
    User,
)

if TYPE_CHECKING:
    from seminare.contests.models import Contest
    from seminare.problems.models import ProblemSet

CONFIGURABLE_TYPES = [
    NotificationType.PROBLEM_SET,
    NotificationType.SUBMIT_GRADED,
    NotificationType.POST,
]

DEFAULT_CHANNELS = [NotificationChannel.SITE]

FORCED_CHANNELS = {
    NotificationType.ADMIN: [NotificationChannel.SITE, NotificationChannel.EMAIL],
}


def get_channels_map(
    users: Iterable[User], contest: "Contest", type: NotificationType
) -> dict[int, list[NotificationChannel]]:
    users = list(users)

    if type in FORCED_CHANNELS:
        return {user.id: FORCED_CHANNELS[type] for user in users}

    preferences = {
        preference.user_id: [
            NotificationChannel(channel) for channel in preference.channels
        ]
        for preference in NotificationPreferences.objects.filter(
            user__in=users, contest=contest, type=type.value
        )
    }

    return {user.id: preferences.get(user.id, DEFAULT_CHANNELS) for user in users}


def contest_participants(contest: "Contest") -> QuerySet[User]:
    enrolled = Q(enrollment__problem_set__contest=contest)

    return (
        User.objects.filter(enrolled | Q(contestrole__contest=contest))
        .distinct()
        .order_by("id")
    )


def previous_problem_set_participants(problem_set: "ProblemSet") -> QuerySet[User]:
    return (
        User.objects.filter(
            enrollment__problem_set__contest=problem_set.contest_id,
            enrollment__problem_set__end_date__lte=problem_set.start_date,
        )
        .exclude(id__in=problem_set.enrollment_set.values("user_id"))
        .distinct()
        .order_by("id")
    )


def notify(
    users: Iterable[User],
    contest: Contest,
    type: NotificationType,
    title: str,
    content: str,
    link: str = "",
) -> None:
    from seminare.users.tasks import mail_notification, push_notification

    users = list(users)
    if not users:
        return

    channels_map = get_channels_map(users, contest, type)

    Notification.objects.bulk_create(
        [
            Notification(
                user_id=user.id,
                contest=contest,
                type=type.value,
                title=title,
                content=content,
                link=link,
            )
            for user in users
            if NotificationChannel.SITE in channels_map[user.id]
        ]
    )

    for user in users:
        if NotificationChannel.EMAIL in channels_map[user.id] and user.email:
            mail_notification.delay(
                email=user.email,
                contest_id=contest.id,
                title=title,
                content=content,
                link=link,
            )

    push_user_ids = [
        user.id for user in users if NotificationChannel.PUSH in channels_map[user.id]
    ]
    if push_user_ids:
        subscribed_ids = set(
            PushSubscription.objects.filter(user_id__in=push_user_ids)
            .values_list("user_id", flat=True)
            .distinct()
        )
        for user_id in subscribed_ids:
            push_notification.delay(
                user_id=user_id,
                contest_id=contest.id,
                title=title,
                content=content,
                link=link,
            )


def schedule_debug_notification(user_id: int, contest_id: int) -> None:
    timer = threading.Timer(60, _send_debug_notification, args=(user_id, contest_id))
    timer.daemon = True
    timer.start()


def _send_debug_notification(user_id: int, contest_id: int) -> None:
    from django.db import close_old_connections

    from seminare.contests.models import Contest
    from seminare.users.tasks import push_notification

    close_old_connections()
    try:
        contest = Contest.objects.select_related("site").filter(id=contest_id).first()
        if contest is None or not User.objects.filter(id=user_id).exists():
            return

        title = "Testovacie upozornenie"
        content = "Toto je testovacie upozornenie odoslané minútu po kliknutí."
        link = contest.absolute_url("/")
        Notification.objects.create(
            user_id=user_id,
            contest=contest,
            type=NotificationType.ADMIN,
            title=title,
            content=content,
            link=link,
        )
        push_notification(user_id, contest_id, title, content, link)
    finally:
        close_old_connections()

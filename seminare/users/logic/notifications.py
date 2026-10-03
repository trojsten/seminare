from collections.abc import Iterable
from typing import TYPE_CHECKING

from django.db.models import Q, QuerySet

from seminare.users.models import (
    Notification,
    NotificationChannel,
    NotificationPreferences,
    NotificationType,
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
    from seminare.users.tasks import mail_notification

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

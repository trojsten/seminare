from django import template
from django.urls import reverse

from seminare.content.models import MenuItem
from seminare.contests.utils import get_current_contest
from seminare.users.logic.permissions import is_contest_organizer
from seminare.users.models import Notification

register = template.Library()


@register.inclusion_tag("navbar/menu.html", takes_context=True)
def navbar_menu(context):
    contest = get_current_contest(context["request"])
    context["items"] = list(
        MenuItem.objects.filter(group__contest=contest).select_related("group").all()
    )

    user = context["user"]
    if not user.is_authenticated:
        return context

    user_section = context["user_section"] = list()

    if is_contest_organizer(user, contest):
        user_section.append(
            MenuItem(
                title="Organizátorské rozhranie",
                icon="mdi:account-tie",
                url=reverse("org:contest_dashboard"),
            )
        )

    logout = MenuItem(
        title="Odhlásiť sa",
        icon="mdi:logout",
        url=reverse("oidc_logout"),
    )
    setattr(logout, "post", True)

    user_section.extend(
        [
            MenuItem(
                title="Môj profil",
                icon="mdi:user",
                url="https://id.trojsten.sk/",
            ),
            logout,
        ]
    )

    notifications = context["notifications"] = Notification.objects.filter(user=user)[
        :5
    ]
    has_unread_notifications = context["has_unread_notifications"] = (
        Notification.objects.filter(user=user, viewed_at__isnull=True).exists()
    )
    notification_section = context["notification_section"] = list()

    if notifications:
        if has_unread_notifications:
            mark_all_read = MenuItem(
                title="Označiť ako prečítané",
                icon="mdi:eye",
                url=reverse("notification_mark_all_read"),
            )
            setattr(mark_all_read, "post", True)
            notification_section.append(mark_all_read)

        delete_all = MenuItem(
            title="Vymazať všetky",
            icon="mdi:trash",
            url=reverse("notification_delete_all"),
        )
        setattr(delete_all, "post", True)
        notification_section.append(delete_all)

    notification_section.append(
        MenuItem(
            title="Nastavenia upozornení",
            icon="mdi:notification-settings",
            url=reverse("notification_settings"),
        )
    )

    return context
